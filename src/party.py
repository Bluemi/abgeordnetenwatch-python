class Party:
    def __init__(self, id: int, label: str):
        self.id = id
        self.label = label

    @staticmethod
    def from_json(data: dict):
        return Party(
            id=data['id'],
            label=data['label']
        )

    def get_api_url(self):
        return "https://www.abgeordnetenwatch.de/api/v2/parties/{}".format(self.id)

    def __repr__(self):
        return 'Party(id={}, label={})'.format(self.id, self.label)

    def to_json(self):
        return dict(
            id=self.id,
            label=self.label,
        )
