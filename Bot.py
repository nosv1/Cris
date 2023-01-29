import discord

class Bot(discord.Bot):
    def __init__(self, debug=False, *args, **options):
        super().__init__(*args, **options)

        self.debug = debug
        self._developer_ids = [
            405944496665133058,  # Mo#9991
        ]

    def is_developer(self, user: discord.User) -> bool:
        return user.id in self._developer_ids