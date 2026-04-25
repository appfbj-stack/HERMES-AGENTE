import { FormEvent, useState } from 'react'
import { Send, Smile, Paperclip } from 'lucide-react'

interface Props {
  disabled?: boolean
  onSend: (text: string) => void
}

export default function MessageInput({ disabled, onSend }: Props) {
  const [value, setValue] = useState('')

  function submit(e: FormEvent) {
    e.preventDefault()
    const text = value.trim()
    if (!text || disabled) return
    onSend(text)
    setValue('')
  }

  return (
    <form
      onSubmit={submit}
      className="flex items-center gap-2 px-3 py-2 bg-wa-bg border-t border-wa-border"
    >
      <button
        type="button"
        className="p-2 text-wa-subtext hover:text-wa-text"
        title="Emoji"
      >
        <Smile size={20} />
      </button>
      <button
        type="button"
        className="p-2 text-wa-subtext hover:text-wa-text"
        title="Anexar"
      >
        <Paperclip size={20} />
      </button>
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={disabled ? 'IA pausada' : 'Digite uma mensagem'}
        disabled={disabled}
        className="flex-1 px-4 py-2 rounded-full bg-white border border-wa-border outline-none disabled:opacity-60"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="p-3 rounded-full bg-wa-green text-white hover:bg-wa-greenDark disabled:opacity-50"
        title="Enviar"
      >
        <Send size={18} />
      </button>
    </form>
  )
}
