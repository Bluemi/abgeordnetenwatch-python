class Party:
    def __init__(self, iden: int, label: str):
        self.iden = iden
        self.label = label

    @staticmethod
    def from_json(data: dict):
        return Party(
            iden=data['id'],
            label=data['label']
        )

    def get_api_url(self):
        return "https://www.abgeordnetenwatch.de/api/v2/parties/{}".format(self.iden)

    def __repr__(self):
        return 'Party(id={}, label={})'.format(self.iden, self.label)

    def to_json(self):
        return dict(
            id=self.iden,
            label=self.label,
        )
