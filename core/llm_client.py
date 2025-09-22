from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import logging
from configs.loader import AZURE_OPENAI_API_KEY
from core.structured_outputs_models import (
    RispostaAccessibileFinale,
    EventoAccessibile,
    DescrizioneAccessibile,
)
from core.bot_enums import BotCommandsEnum

# Global LLM instance (reused across Lambda invocations)
_llm_instance = None

logger = logging.getLogger("bot")


def get_llm():
    """Get or create LLM instance (singleton pattern for Lambda efficiency)"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = AzureChatOpenAI(
            azure_endpoint="https://poc-openai-test.openai.azure.com/",
            azure_deployment="gpt-4o-mini",
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2024-10-01-preview",
            temperature=0.5,
            max_tokens=500,
            max_retries=0,
        )
    return _llm_instance


def llm_process_image_from_url(
    image_url: str,
    image_caption: str | None = None,
    image_reply_to_text: str | None = None,
    command_text: str | None = None,
) -> str:
    # Setup LLM with structured output
    llm = get_llm()

    match command_text:
        case BotCommandsEnum.DESCRIVI.value:
            structured_llm = llm.with_structured_output(
                DescrizioneAccessibile, include_raw=True
            )
        case BotCommandsEnum.DESCRIVI_EVENTO.value:
            structured_llm = llm.with_structured_output(
                EventoAccessibile, include_raw=True
            )
        case _:
            structured_llm = llm.with_structured_output(
                RispostaAccessibileFinale, include_raw=True
            )

    # Prepare image input
    # NOTE: explicit type cast to handle pyright error due to list being invariant
    image_content: list[str | dict] = [
        {
            "type": "image_url",
            "image_url": {
                "url": image_url,
                "detail": "low",  # Use low detail for cost efficiency
            },
        }
    ]

    if image_caption:
        image_content.append(
            {
                "type": "text",
                "text": f"Questo è il commento dell'utente che ha inviato la foto: {image_caption}",  # codespell:ignore
            }
        )
    if image_reply_to_text:
        image_content.append(
            {
                "type": "text",
                "text": f"Questo è il commento di un altro utente che potrebbe contenere informazioni ulteriori come dettagli o correzzioni, o un contesto migliore: {image_reply_to_text}",
            }
        )

    prompt = [
        SystemMessage(
            "Sei un bot di Telegram che aiuta le persone con disabilità visive a comprendere il contenuto delle immagini che vengono inviate da utenti."
            "Fornisci descrizioni dettagliate e accessibili basate sulle informazioni visive e testuali disponibili."
            "Se è presente del testo nell'immagine, riportalo fedelmente."
            "Se non hai informazioni accurate, evita assolutamente di inventare dettagli o ripotarli come fatti."
            ""
            "Tieni a mente che il bot di Telegram fa parte del gruppo di nome 'Poliamore Milano' che tratta di non-monogamia consensuale ed etica con valori di: inclusività, rispetto, transfemminilità, e comunità intersezionale."  # codespell:ignore
            "Assumi che gli utenti del bot condividano questi valori e che le immagini inviate siano in linea con questi valori."
            "Nel rispondere usa un linguaggio inclusivo e rispettoso, usando il femminile come genere neutro, o l'asterisco (*) o lo schwa (ə)."
        ),
        HumanMessage(image_content),
    ]
    # Get description from LLM
    response = structured_llm.invoke(prompt)
    risposta_accessibile = response["parsed"]
    description = str(risposta_accessibile)
    return description
