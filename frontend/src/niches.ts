export interface Niche {
  key: string;
  label: string;
  emoji: string;
  plan: string;
  credits: number;
  systemPrompt: string;
  botDisplayName: string;
  welcomeMessage: string;
}

export const NICHES: Niche[] = [
  {
    key: "barbearia",
    label: "Barbearia / Salao",
    emoji: "💈",
    plan: "starter",
    credits: 1000,
    systemPrompt:
      "Voce e o assistente virtual de uma barbearia/salao. Agenda horarios, apresenta servicos e precos, responde duvidas de clientes de forma simpatica e profissional.",
    botDisplayName: "Assistente Barbearia",
    welcomeMessage: "Ola! Bem-vindo a nossa barbearia. Como posso te ajudar hoje?",
  },
  {
    key: "assistencia",
    label: "Assistencia Tecnica",
    emoji: "🔧",
    plan: "starter",
    credits: 1000,
    systemPrompt:
      "Voce e o assistente virtual de uma assistencia tecnica. Recebe chamados, informa prazos e precos, orienta sobre garantias e status de reparo.",
    botDisplayName: "Assistente Tecnico",
    welcomeMessage: "Ola! Precisa de assistencia tecnica? Me conta o problema do seu aparelho.",
  },
  {
    key: "imobiliaria",
    label: "Imobiliaria",
    emoji: "🏠",
    plan: "pro",
    credits: 2000,
    systemPrompt:
      "Voce e o assistente virtual de uma imobiliaria. Apresenta imoveis, agenda visitas, responde duvidas sobre compra, venda e aluguel de forma clara e objetiva.",
    botDisplayName: "Assistente Imobiliario",
    welcomeMessage: "Ola! Procurando imovel para comprar, vender ou alugar? Posso te ajudar!",
  },
  {
    key: "engenharia",
    label: "Engenharia / Construcao",
    emoji: "🏗️",
    plan: "pro",
    credits: 2000,
    systemPrompt:
      "Voce e o assistente virtual de uma empresa de engenharia e construcao. Responde sobre projetos, orcamentos, prazos e materiais de forma tecnica e profissional.",
    botDisplayName: "Assistente Engenharia",
    welcomeMessage: "Ola! Posso te ajudar com informacoes sobre projetos e construcao. O que voce precisa?",
  },
  {
    key: "advocacia",
    label: "Advocacia / Juridico",
    emoji: "⚖️",
    plan: "pro",
    credits: 2000,
    systemPrompt:
      "Voce e o assistente virtual de um escritorio de advocacia. Recebe consultas iniciais, agenda reunioes e orienta sobre areas de atuacao. NUNCA fornece aconselhamento juridico definitivo.",
    botDisplayName: "Assistente Juridico",
    welcomeMessage: "Ola! Posso ajudar com informacoes sobre nossos servicos juridicos. Como posso te orientar?",
  },
  {
    key: "clinica",
    label: "Clinica / Saude",
    emoji: "🏥",
    plan: "pro",
    credits: 2000,
    systemPrompt:
      "Voce e o assistente virtual de uma clinica de saude. Agenda consultas, informa sobre especialidades e convenios, responde duvidas gerais. NUNCA da diagnosticos medicos.",
    botDisplayName: "Assistente Clinica",
    welcomeMessage: "Ola! Posso ajudar a agendar sua consulta ou tirar duvidas sobre nossa clinica.",
  },
  {
    key: "restaurante",
    label: "Restaurante / Delivery",
    emoji: "🍽️",
    plan: "starter",
    credits: 1000,
    systemPrompt:
      "Voce e o assistente virtual de um restaurante. Apresenta cardapio, recebe pedidos, informa sobre tempo de entrega e promocoes de forma simpatica e agil.",
    botDisplayName: "Assistente Restaurante",
    welcomeMessage: "Ola! Bem-vindo! Quer ver nosso cardapio ou fazer um pedido?",
  },
  {
    key: "mecanica",
    label: "Mecanica / Auto Center",
    emoji: "🔩",
    plan: "pro",
    credits: 3000,
    systemPrompt:
      "Voce e o assistente virtual de uma oficina mecanica / auto center. Atende clientes de forma prestativa, clara e confiante. Recebe orcamentos, agenda servicos, informa sobre revisao, alinhamento, balanceamento, troca de oleo, freios, suspensao e eletrica. NUNCA prometa preco final sem avaliacao presencial.",
    botDisplayName: "Assistente Mecanica",
    welcomeMessage: "Ola! Sou o assistente do Auto Center. Como posso ajudar? Informe o problema do seu veiculo.",
  },
  {
    key: "fotografia",
    label: "Fotografia / Estudio",
    emoji: "📸",
    plan: "pro",
    credits: 3000,
    systemPrompt:
      "Voce e o assistente virtual de um estudio de fotografia profissional. Apresenta servicos de ensaios individuais, de casal, familia, gestante, newborn, corporativo, eventos, formaturas e casamentos. Agenda sessoes, informa pacotes e precos. Tom criativo, elegante e inspirador.",
    botDisplayName: "Assistente Estudio",
    welcomeMessage: "Ola! Seja bem-vindo ao nosso Estudio de Fotografia. Que tipo de ensaio voce esta planejando?",
  },
];

export function getNicheByKey(key: string): Niche | undefined {
  return NICHES.find((n) => n.key === key);
}
