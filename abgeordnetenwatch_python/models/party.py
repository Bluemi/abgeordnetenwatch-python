from pydantic import BaseModel


class Party(BaseModel):
    id: int
    label: str

    def get_api_url(self) -> str:
        return "https://www.abgeordnetenwatch.de/api/v2/parties/{}".format(self.id)

    def __repr__(self) -> str:
        return 'Party(id={}, label={})'.format(self.id, self.label)
