import json
import secrets
from datetime import datetime, timezone, timedelta
from typing import Any

import requests
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import get_password_hash, verify_password
from app.deps import (
    get_current_tenant,
    get_current_user,
    require_content_publisher_module,
    require_instagram_module,
    require_youtube_module,
    tenant_has_module,
)
from app.models import SocialIntegrationAccount, SocialPost, Tenant, User

router = APIRouter(prefix="/integrations", tags=["integrations"])
logger = get_logger(__name__)


# ============== OAUTH CONFIGURAÇÕES ==============

# Instagram OAuth (Meta/Facebook)
INSTAGRAM_OAUTH_URL = "https://www.facebook.com/v18.0/dialog/oauth"
INSTAGRAM_TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
INSTAGRAM_API_BASE = "https://graph.facebook.com/v18.0"

# YouTube OAuth (Google)
YOUTUBE_OAUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
YOUTUBE_TOKEN_URL = "https://oauth2.googleapis.com/token"
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


# ============== SCHEMAS ==============

class InstagramConnectRequest(BaseModel):
    """Configuração para conectar Instagram"""
    client_id: str
    redirect_uri: str
    scope: str = "instagram_basic,instagram_content_publish,pages_show_list"


class YouTubeConnectRequest(BaseModel):
    """Configuração para conectar YouTube"""
    client_id: str
    redirect_uri: str
    scope: str = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube"


class SocialPostCreate(BaseModel):
    """Criar nova publicação"""
    title: str
    content: str
    media_type: str  # image, video, reel, short
    media_url: str
    thumbnail_url: str | None = None
    hashtags: str | None = None
    caption: str | None = None
    platforms: list[str]  # ["instagram", "youtube"]
    scheduled_at: str | None = None


class SocialPostUpdate(BaseModel):
    """Atualizar publicação"""
    title: str | None = None
    content: str | None = None
    media_type: str | None = None
    media_url: str | None = None
    thumbnail_url: str | None = None
    hashtags: str | None = None
    caption: str | None = None
    platforms: list[str] | None = None
    scheduled_at: str | None = None
    status: str | None = None


# ============== FUNÇÕES AUXILIARES ==============

def encrypt_token(token: str) -> str:
    """Criptografa token usando uma chave fixa (em produção, usar variável de ambiente)"""
    from cryptography.fernet import Fernet
    
    # Em produção, usar uma chave secreta do vault ou variável de ambiente
    secret_key = get_settings().jwt_secret.encode()[:32].ljust(32, b'=')
    fernet = Fernet(secret_key)
    return fernet.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    """Descriptografa token"""
    from cryptography.fernet import Fernet
    
    secret_key = get_settings().jwt_secret.encode()[:32].ljust(32, b'=')
    fernet = Fernet(secret_key)
    return fernet.decrypt(encrypted_token.encode()).decode()


def _require_tenant_module_or_403(db: Session, tenant_id: int, module_key: str, label: str) -> None:
    if not tenant_has_module(db, tenant_id, module_key):
        raise HTTPException(status_code=403, detail=f"Módulo {label} não está ativo neste plano.")


# ============== INSTAGRAM OAUTH ==============

@router.get("/instagram/connect")
def instagram_connect(
    tenant_id: int = Query(...),
    user_id: int = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str = Query("instagram_basic,instagram_content_publish,pages_show_list"),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _: object = Depends(require_instagram_module),
):
    """Inicia o fluxo OAuth do Instagram"""
    if tenant_id != tenant.id or user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Tenant ou usuário inválido para esta integração")

    state = secrets.token_urlsafe(16)
    
    # Guardar o state no cache/sessão por 5 minutos (em produção usar Redis)
    # Por enquanto, vamos retornar o URL direto
    
    oauth_url = (
        f"{INSTAGRAM_OAUTH_URL}"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&response_type=code"
        f"&state={state}"
    )
    
    return {"oauth_url": oauth_url, "state": state}


@router.get("/instagram/callback")
async def instagram_callback(
    code: str = Query(...),
    state: str = Query(...),
    tenant_id: int = Query(...),
    user_id: int = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    client_secret: str = Query(...),
    db: Session = Depends(get_db),
):
    """Callback OAuth do Instagram"""
    _require_tenant_module_or_403(db, tenant_id, "instagram", "Instagram")

    try:
        # Trocar código por token de acesso
        token_response = requests.post(INSTAGRAM_TOKEN_URL, data={
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        })
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Falha ao obter token do Instagram")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # Obter informações do usuário do Instagram
        user_response = requests.get(
            f"{INSTAGRAM_API_BASE}/me",
            params={"fields": "id,username,account_type", "access_token": access_token}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Falha ao obter dados do usuário")
        
        user_data = user_response.json()
        
        # Obter imagem do perfil
        profile_response = requests.get(
            f"{INSTAGRAM_API_BASE}/{user_data['id']}",
            params={"fields": "profile_picture_url,username", "access_token": access_token}
        )
        
        profile_data = profile_response.json() if profile_response.status_code == 200 else {}
        
        # Criar integração
        integration = SocialIntegrationAccount(
            tenant_id=tenant_id,
            provider="instagram",
            provider_user_id=user_data.get("id"),
            username=user_data.get("username", ""),
            display_name=user_data.get("username", ""),
            avatar_url=profile_data.get("profile_picture_url"),
            access_token=encrypt_token(access_token),
            scope="instagram_basic,instagram_content_publish,pages_show_list",
            status="active",
        )
        
        db.add(integration)
        db.commit()
        db.refresh(integration)
        
        return {
            "success": True,
            "message": "Instagram conectado com sucesso!",
            "username": integration.username,
            "display_name": integration.display_name,
        }
        
    except requests.RequestException as exc:
        logger.exception("Falha de comunicação ao conectar Instagram para tenant_id=%s", tenant_id)
        raise HTTPException(status_code=500, detail=f"Erro na comunicação com Instagram: {str(exc)}") from exc
    except HTTPException:
        raise
    except (ValueError, KeyError, TypeError) as exc:
        logger.exception("Falha ao processar callback do Instagram para tenant_id=%s", tenant_id)
        raise HTTPException(status_code=500, detail=f"Erro ao conectar Instagram: {str(exc)}") from exc


# ============== YOUTUBE OAUTH ==============

@router.get("/youtube/connect")
def youtube_connect(
    tenant_id: int = Query(...),
    user_id: int = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str = Query("https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube"),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _: object = Depends(require_youtube_module),
):
    """Inicia o fluxo OAuth do YouTube"""
    if tenant_id != tenant.id or user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Tenant ou usuário inválido para esta integração")

    state = secrets.token_urlsafe(16)
    
    oauth_url = (
        f"{YOUTUBE_OAUTH_URL}"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&response_type=code"
        f"&access_type=offline"
        f"&state={state}"
        f"&prompt=consent"
    )
    
    return {"oauth_url": oauth_url, "state": state}


@router.get("/youtube/callback")
async def youtube_callback(
    code: str = Query(...),
    state: str = Query(...),
    tenant_id: int = Query(...),
    user_id: int = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    client_secret: str = Query(...),
    db: Session = Depends(get_db),
):
    """Callback OAuth do YouTube"""
    _require_tenant_module_or_403(db, tenant_id, "youtube", "YouTube")

    try:
        # Trocar código por token de acesso
        token_response = requests.post(YOUTUBE_TOKEN_URL, data={
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
            "grant_type": "authorization_code",
        })
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Falha ao obter token do YouTube")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)
        
        # Obter informações do canal do YouTube
        headers = {"Authorization": f"Bearer {access_token}"}
        channel_response = requests.get(
            f"{YOUTUBE_API_BASE}/channels",
            params={"part": "snippet,statistics", "mine": "true"},
            headers=headers
        )
        
        if channel_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Falha ao obter dados do canal")
        
        channel_data = channel_response.json()
        if not channel_data.get("items"):
            raise HTTPException(status_code=400, detail="Canal não encontrado")
        
        channel = channel_data["items"][0]
        snippet = channel["snippet"]
        statistics = channel["statistics"]
        
        # Criar integração
        integration = SocialIntegrationAccount(
            tenant_id=tenant_id,
            provider="youtube",
            provider_user_id=channel["id"],
            username=snippet.get("title", ""),
            display_name=snippet.get("title", ""),
            avatar_url=snippet.get("thumbnails", {}).get("default", {}).get("url"),
            access_token=encrypt_token(access_token),
            refresh_token=encrypt_token(refresh_token) if refresh_token else None,
            token_expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            scope="youtube.upload,youtube",
            status="active",
        )
        
        db.add(integration)
        db.commit()
        db.refresh(integration)
        
        return {
            "success": True,
            "message": "YouTube conectado com sucesso!",
            "channel_name": integration.display_name,
            "subscribers": statistics.get("subscriberCount", "0"),
        }
        
    except requests.RequestException as exc:
        logger.exception("Falha de comunicação ao conectar YouTube para tenant_id=%s", tenant_id)
        raise HTTPException(status_code=500, detail=f"Erro na comunicação com YouTube: {str(exc)}") from exc
    except HTTPException:
        raise
    except (ValueError, KeyError, TypeError) as exc:
        logger.exception("Falha ao processar callback do YouTube para tenant_id=%s", tenant_id)
        raise HTTPException(status_code=500, detail=f"Erro ao conectar YouTube: {str(exc)}") from exc


# ============== GESTÃO DE CONTAS ==============

@router.get("/accounts")
def list_accounts(
    provider: str | None = Query(None),
    db: Session = Depends(get_db),
    tenant=Depends(get_current_tenant),
    _: object = Depends(require_content_publisher_module),
):
    """Listar contas conectadas"""
    query = db.query(SocialIntegrationAccount).filter(SocialIntegrationAccount.tenant_id == tenant.id)
    
    if provider:
        query = query.filter(SocialIntegrationAccount.provider == provider)
    
    accounts = query.order_by(SocialIntegrationAccount.created_at.desc()).all()
    
    return {
        "accounts": [
            {
                "id": acc.id,
                "provider": acc.provider,
                "username": acc.username,
                "display_name": acc.display_name,
                "avatar_url": acc.avatar_url,
                "status": acc.status,
                "created_at": acc.created_at,
                "last_webhook_at": acc.last_webhook_at,
            }
            for acc in accounts
        ]
    }


@router.delete("/disconnect/{account_id}")
def disconnect_account(
    account_id: int,
    db: Session = Depends(get_db),
    tenant=Depends(get_current_tenant),
    _: object = Depends(require_content_publisher_module),
):
    """Desconectar conta social"""
    account = db.query(SocialIntegrationAccount).filter(
        SocialIntegrationAccount.id == account_id,
        SocialIntegrationAccount.tenant_id == tenant.id,
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    db.delete(account)
    db.commit()
    
    return {"success": True, "message": "Conta desconectada com sucesso"}


# ============== PUBLICADOR DE CONTEÚDO ==============

@router.get("/posts")
def list_posts(
    status: str | None = Query(None),
    platform: str | None = Query(None),
    db: Session = Depends(get_db),
    tenant=Depends(get_current_tenant),
    _: object = Depends(require_content_publisher_module),
):
    """Listar publicações"""
    query = db.query(SocialPost).filter(SocialPost.tenant_id == tenant.id)
    
    if status:
        query = query.filter(SocialPost.status == status)
    
    if platform:
        query = query.filter(SocialPost.platforms.contains(platform))
    
    posts = query.order_by(SocialPost.created_at.desc()).all()
    
    return {
        "posts": [
            {
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "media_type": post.media_type,
                "media_url": post.media_url,
                "thumbnail_url": post.thumbnail_url,
                "hashtags": post.hashtags,
                "caption": post.caption,
                "platforms": json.loads(post.platforms) if post.platforms else [],
                "scheduled_at": post.scheduled_at,
                "published_at": post.published_at,
                "status": post.status,
                "instagram_post_id": post.instagram_post_id,
                "instagram_media_url": post.instagram_media_url,
                "youtube_video_id": post.youtube_video_id,
                "youtube_video_url": post.youtube_video_url,
                "error_message": post.error_message,
                "created_at": post.created_at,
            }
            for post in posts
        ]
    }


@router.post("/posts")
def create_post(
    payload: SocialPostCreate,
    db: Session = Depends(get_db),
    tenant=Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _: object = Depends(require_content_publisher_module),
):
    """Criar nova publicação"""
    post = SocialPost(
        tenant_id=tenant.id,
        title=payload.title,
        content=payload.content,
        media_type=payload.media_type,
        media_url=payload.media_url,
        thumbnail_url=payload.thumbnail_url,
        hashtags=payload.hashtags,
        caption=payload.caption,
        platforms=json.dumps(payload.platforms),
        scheduled_at=datetime.fromisoformat(payload.scheduled_at) if payload.scheduled_at else None,
        status="scheduled" if payload.scheduled_at else "draft",
        created_by_user_id=current_user.id,
    )
    
    db.add(post)
    db.commit()
    db.refresh(post)
    
    return {
        "id": post.id,
        "title": post.title,
        "status": post.status,
        "scheduled_at": post.scheduled_at,
        "platforms": json.loads(post.platforms),
    }


@router.post("/posts/{post_id}/publish")
async def publish_post(
    post_id: int,
    db: Session = Depends(get_db),
    tenant=Depends(get_current_tenant),
    _: object = Depends(require_content_publisher_module),
):
    """Publicar post"""
    post = db.query(SocialPost).filter(SocialPost.id == post_id, SocialPost.tenant_id == tenant.id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    
    try:
        platforms = json.loads(post.platforms)
        results = []
        
        # Publicar no Instagram
        if "instagram" in platforms:
            integration = db.query(SocialIntegrationAccount).filter(
                SocialIntegrationAccount.provider == "instagram",
                SocialIntegrationAccount.tenant_id == tenant.id,
            ).first()
            
            if integration:
                try:
                    access_token = decrypt_token(integration.access_token)
                    
                    # Upload de mídia
                    upload_response = requests.post(
                        f"{INSTAGRAM_API_BASE}/{integration.provider_user_id}/media",
                        params={
                            "video_url": post.media_url if post.media_type in ["video", "reel"] else None,
                            "image_url": post.media_url if post.media_type == "image" else None,
                            "caption": post.caption or "",
                            "access_token": access_token
                        }
                    )
                    
                    if upload_response.status_code == 200:
                        media_data = upload_response.json()
                        post.instagram_post_id = media_data.get("id")
                        post.instagram_media_url = media_data.get("media_url")
                        results.append({"platform": "instagram", "success": True, "post_id": post.instagram_post_id})
                    else:
                        results.append({"platform": "instagram", "success": False, "error": "Erro ao publicar"})
                        
                except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
                    logger.warning(
                        "Falha ao publicar no Instagram para tenant_id=%s post_id=%s: %s",
                        tenant.id,
                        post.id,
                        exc,
                    )
                    results.append({"platform": "instagram", "success": False, "error": str(exc)})
        
        # Publicar no YouTube
        if "youtube" in platforms:
            integration = db.query(SocialIntegrationAccount).filter(
                SocialIntegrationAccount.provider == "youtube",
                SocialIntegrationAccount.tenant_id == tenant.id,
            ).first()
            
            if integration:
                try:
                    access_token = decrypt_token(integration.access_token)
                    
                    # Upload de vídeo
                    headers = {"Authorization": f"Bearer {access_token}"}
                    
                    # Inicializar upload
                    upload_response = requests.post(
                        f"{YOUTUBE_API_BASE}/videos?uploadType=resumable&part=snippet,status",
                        headers={
                            **headers,
                            "Content-Type": "application/json; charset=utf-8"
                        },
                        json={
                            "snippet": {
                                "title": post.title,
                                "description": post.caption or post.content,
                                "tags": post.hashtags.split(",") if post.hashtags else []
                            },
                            "status": {
                                "privacyStatus": "public",
                                "selfDeclaredMadeForKids": False
                            }
                        }
                    )
                    
                    if upload_response.status_code == 200:
                        upload_data = upload_response.json()
                        post.youtube_video_id = upload_data.get("id")
                        results.append({"platform": "youtube", "success": True, "video_id": post.youtube_video_id})
                    else:
                        results.append({"platform": "youtube", "success": False, "error": "Erro ao publicar"})
                        
                except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
                    logger.warning(
                        "Falha ao publicar no YouTube para tenant_id=%s post_id=%s: %s",
                        tenant.id,
                        post.id,
                        exc,
                    )
                    results.append({"platform": "youtube", "success": False, "error": str(exc)})
        
        # Atualizar status
        if any(r["success"] for r in results):
            post.status = "published"
            post.published_at = datetime.now(timezone.utc)
        else:
            post.status = "failed"
            post.error_message = ", ".join([r.get("error", "") for r in results if not r["success"]])
        
        db.commit()
        
        return {
            "success": True,
            "post_id": post.id,
            "results": results,
            "status": post.status
        }
        
    except HTTPException:
        raise
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        post.status = "failed"
        post.error_message = str(exc)
        db.commit()
        logger.exception("Falha ao publicar post social tenant_id=%s post_id=%s", tenant.id, post.id)
        raise HTTPException(status_code=500, detail=f"Erro ao publicar: {str(exc)}") from exc


@router.patch("/posts/{post_id}")
def update_post(
    post_id: int,
    payload: SocialPostUpdate,
    db: Session = Depends(get_db),
    tenant=Depends(get_current_tenant),
    _: object = Depends(require_content_publisher_module),
):
    """Atualizar publicação"""
    post = db.query(SocialPost).filter(SocialPost.id == post_id, SocialPost.tenant_id == tenant.id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    
    data = payload.model_dump(exclude_unset=True)
    
    if "scheduled_at" in data and data["scheduled_at"]:
        data["scheduled_at"] = datetime.fromisoformat(data["scheduled_at"])
    
    if "platforms" in data:
        data["platforms"] = json.dumps(data["platforms"])
    
    for key, value in data.items():
        setattr(post, key, value)
    
    db.commit()
    db.refresh(post)
    
    return {"id": post.id, "title": post.title, "status": post.status}


@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    tenant=Depends(get_current_tenant),
    _: object = Depends(require_content_publisher_module),
):
    """Deletar publicação"""
    post = db.query(SocialPost).filter(SocialPost.id == post_id, SocialPost.tenant_id == tenant.id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    
    db.delete(post)
    db.commit()
    
    return {"success": True, "message": "Post deletado com sucesso"}


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    tenant=Depends(get_current_tenant),
    _: object = Depends(require_content_publisher_module),
):
    """Estatísticas das integrações"""
    total_accounts = db.query(SocialIntegrationAccount).filter(SocialIntegrationAccount.tenant_id == tenant.id).count()
    active_accounts = db.query(SocialIntegrationAccount).filter(
        SocialIntegrationAccount.tenant_id == tenant.id,
        SocialIntegrationAccount.status == "active"
    ).count()
    
    instagram_accounts = db.query(SocialIntegrationAccount).filter(
        SocialIntegrationAccount.tenant_id == tenant.id,
        SocialIntegrationAccount.provider == "instagram"
    ).count()
    
    youtube_accounts = db.query(SocialIntegrationAccount).filter(
        SocialIntegrationAccount.tenant_id == tenant.id,
        SocialIntegrationAccount.provider == "youtube"
    ).count()
    
    total_posts = db.query(SocialPost).filter(SocialPost.tenant_id == tenant.id).count()
    published_posts = db.query(SocialPost).filter(
        SocialPost.tenant_id == tenant.id,
        SocialPost.status == "published"
    ).count()
    scheduled_posts = db.query(SocialPost).filter(
        SocialPost.tenant_id == tenant.id,
        SocialPost.status == "scheduled"
    ).count()
    
    return {
        "accounts": {
            "total": total_accounts,
            "active": active_accounts,
            "instagram": instagram_accounts,
            "youtube": youtube_accounts
        },
        "posts": {
            "total": total_posts,
            "published": published_posts,
            "scheduled": scheduled_posts,
            "draft": total_posts - published_posts - scheduled_posts
        }
    }
