from constants import ENTRY_CHANNEL, SERVER_ID


class Entry:
    def __init__(self, author_id, character_id, message_id, votes=0):
        self.author_id = author_id
        self.message_id = message_id
        self.character_id = character_id
        self.votes = votes

    @property
    def message_link(self):
        return f"https://canary.discordapp.com/channels/{SERVER_ID}/{ENTRY_CHANNEL}/{self.message_id}"

    @property
    def char_link(self):
        return f"https://ddb.ac/characters/{self.character_id}/"

    def __repr__(self):
        return f"<Entry votes={self.votes}>"
