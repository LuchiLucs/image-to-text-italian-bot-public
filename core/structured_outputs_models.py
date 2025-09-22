from pydantic import BaseModel, Field, ConfigDict
from typing import Union, List


class DescrizioneAccessibile(BaseModel):
    """Modello ottimizzato per la descrizione accessibile di immagini generali individuando:
    1) Oggetto: descrive l'elemento principale o il soggetto dell'immagine
    2) Azione: descrive l'ambiente circostante, lo sfondo o il setting dell'immagine
    3) Contesto: descrive l'ambiente circostante, lo sfondo o il setting dell'immagine
    4) Testo: descrive eventualmente il testo se presente nell'immagine, riportato fedelmente
    5) Significato: descrive eventualmente significati o dettagli visivi importanti per la comprensione che potrebbero non essere ovvi come ad esempio i) simboli politici o religiosi, ii) espressioni e tradizioni culturali, e iii) meme

    """

    descrizione: str = Field(
        ...,
        description="Una descrizione completa che integra Oggetto, Azione, Contesto, ed eventualmente anche Testo e/o Significato aggiuntivi presenti nell'immagine",
    )

    def __str__(self) -> str:
        """Genera una descrizione narrativa completa"""
        return self.descrizione


class EventoAccessibile(BaseModel):
    """Modello per la descrizione accessibile di eventi e locandine

    Usa questo modello se e solo se sono presenti tutti i campi mandatori (quelli non opzionali/None di seguito).
    Non inventare assolutamenti valori per i campi se non sono chiaramente identificabili nell'immagine.
    """

    model_config = ConfigDict(
        extra="forbid",  # Prevents hallucinated fields
        str_strip_whitespace=True,  # Strips whitespace from string fields
    )

    nome_evento: str = Field(
        ...,
        description="Descrive in modo conciso il nome dell'evento o il titolo della locandina solo se chiaramente identificabile nell'immagine",  # codespell:ignore
    )

    data_evento: str | None = Field(
        default=None,
        description="Se presente, descrive la data dell'evento con la formattazione 'il %d %B %Y'. "  # codespell:ignore
        "Se solamente l'informazione puntuale dell'anno non è presente, usa in alternativa la formattazione 'il %d %B'. ",
    )

    ora_evento: str | None = Field(
        default=None,
        description="Se presente, descrive l'ora dell'evento con la formattazione 'alle ore %H:%M' o 'a partire dalle ore %H:%M fino alle ore %H:%M'.",  # codespell:ignore
    )

    descrizione_evento: str | None = Field(
        default=None,
        description="Descrive in modo conciso l'argomento dell'evento",
    )

    organizzatori_evento: List[str] | None = Field(
        default=None,
        description="Descrive in modo conciso il nome o i nomi di chi organizza l'evento eventuali informazioni aggiuntivi come titolo di studio, professione, o breve descrizione",  # codespell:ignore
    )

    contatti_organizzatori: List[str] | None = Field(
        default=None,
        description="Descrive in modo conciso i contatti degli organizzatori dell'evento, come ad esempio e-mails, numeri di telefono, socials",
    )

    luogo_evento: str | None = Field(
        default=None,
        description="Descrive il luogo fisico o virtuale dell'evento. Se fisico, possibilmente un indirizzo completo per la navigazione.",
    )

    altro: str | None = Field(
        default=None,
        description="Descrive eventuali altre informazioni presenti nell'immagine non descritte, come ad esempio la presenza di QR code o di altre informazioni testuali non menzionate",
    )

    def __str__(self) -> str:
        # Creazione di una descrizione testuale strutturata dell'evento
        str_description = f"Evento: {self.nome_evento}\n"

        if self.organizzatori_evento is not None:
            organizzatori = ", ".join(self.organizzatori_evento)
            str_description += f"Organizzato da: {organizzatori}\n"
        if self.descrizione_evento is not None:
            str_description += f"Descrizione: {self.descrizione_evento}\n"
        if self.contatti_organizzatori is not None:
            contatti = ", ".join(self.contatti_organizzatori)
            str_description += f"Contatti: {contatti}\n"
        else:
            str_description += "Contatti: non disponibili\n"
        if self.data_evento is not None and self.ora_evento is not None:
            str_description += f"Data e ora: {self.data_evento}, {self.ora_evento}\n"
        elif self.data_evento is not None and self.ora_evento is None:
            str_description += f"Data: {self.data_evento}\n"
        elif self.data_evento is None and self.ora_evento is not None:
            str_description += f"Ora: {self.ora_evento}\n"
        else:
            str_description += "Data e ora: non disponibili\n"
        if self.luogo_evento is not None:
            str_description += f"Luogo: {self.luogo_evento}\n"
        else:
            str_description += "Luogo: non disponibile\n"
        if self.altro is not None:
            str_description += f"Altro: {self.altro}\n"
        return str_description


class RispostaAccessibileFinale(BaseModel):
    """Modello principale che determina il tipo di risposta"""

    descrizione: Union[DescrizioneAccessibile, EventoAccessibile] = Field(
        ..., description="Descrizione dell'immagine secondo il tipo identificato"
    )

    def __str__(self) -> str:
        """Ottiene il testo finale formattato per l'utente"""
        cls = self.descrizione
        if isinstance(cls, EventoAccessibile):
            return f"Ecco la descrizione dell'evento:\n\n{self.descrizione}"
        elif isinstance(cls, DescrizioneAccessibile):
            return f"Ecco la descrizione dell'immagine:\n\n{self.descrizione}"
        else:
            return "L'immagine non è stata descritta con testo"
