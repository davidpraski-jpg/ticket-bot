import discord
from discord.ext import commands
from discord import app_commands
import os

TOKEN = os.getenv("MTQwMzE3MTMwNTc3NTQzMTY5MA.G68iM4.Np_7WUOI4PgL-ROOit11_LGeHOpLYtS5DUH0HI")  # Token ustaw na Railway w zmiennych środowiskowych
TICKET_CATEGORY_ID = 1403511981285314730
ROLE_ZARZAD_ID = 1403174966819819674

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

open_tickets = set()

@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Zsynchronizowano {len(synced)} komend slash.")
    except Exception as e:
        print(e)

@bot.tree.command(name="ticket", description="Otwórz panel do tworzenia ticketów")
async def ticket_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="System Ticketów",
        description="Kliknij przycisk, aby otworzyć ticket. Możesz mieć tylko jeden otwarty ticket.",
        color=discord.Color.green()
    )
    view = TicketButton()
    await interaction.response.send_message(embed=embed, view=view)

class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Otwórz ticket", style=discord.ButtonStyle.green, custom_id="open_ticket"))

    @discord.ui.button(label="Otwórz ticket", style=discord.ButtonStyle.green)
    async def open_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user

        if user.id in open_tickets:
            await interaction.response.send_message("❌ Masz już otwarty ticket!", ephemeral=True)
            return

        category = discord.utils.get(interaction.guild.categories, id=TICKET_CATEGORY_ID)
        if category is None:
            await interaction.response.send_message("❌ Nie znaleziono kategorii ticketów!", ephemeral=True)
            return

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.get_role(ROLE_ZARZAD_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        ticket_channel = await category.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites)
        open_tickets.add(user.id)

        close_view = CloseButton(user.id)
        await ticket_channel.send(f"{user.mention} Witaj! Opisz swój problem poniżej.", view=close_view)

        await interaction.response.send_message(f"✅ Ticket otwarty: {ticket_channel.mention}", ephemeral=True)

class CloseButton(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="Zamknij ticket", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id and ROLE_ZARZAD_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ Nie możesz zamknąć tego ticketa!", ephemeral=True)
            return

        open_tickets.discard(self.user_id)
        await interaction.channel.delete()

bot.run(TOKEN)
