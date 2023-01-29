import discord

class Bot(discord.Bot):
    def __init__(self, debug=False, *args, **options):
        super().__init__(*args, **options)

        self.debug = debug