import asyncio
import discord
from discord.ext import commands
import os
import json
from datetime import datetime

# Chargement de la configuration
with open('config.json') as f:
    config = json.load(f)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config['prefix'], intents=intents)

ticket_counts = 0
TICKET_CHANNEL_ID = config['ticket_channel_id']  # Charger l'ID du canal à partir de la config
TICKET_PANEL_NAME = config['ticket_panel_name']  # Charger le nom du panneau à partir de la config

async def clear_channel(channel):
    # Récupérer tous les messages du canal et les supprimer
    async for message in channel.history(limit=None):
        await message.delete()


@bot.event
async def on_ready():
    activity = discord.Streaming(name="by t4a#0001", url="https://www.twitch.tv/amouranth")
    await bot.change_presence(activity=activity)

    # Vider le canal de ticket à chaque démarrage du bot
    ticket_channel = bot.get_channel(TICKET_CHANNEL_ID)
    if ticket_channel:
        await clear_channel(ticket_channel)  # Appeler la fonction pour vider le canal

    asyncio.create_task(create_ticket_panel())
    print(f'Success: Le bot est connecté à Discord en tant que {bot.user.name}')



import os  # Assurez-vous d'importer le module os

class Close(discord.ui.View):
    @discord.ui.button(label='Fermer le ticket', style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        global ticket_counts
        
        # Récupérer les informations du salon de transcript
        with open('config.json') as f:
            config = json.load(f)

        transcript_channel_id = config.get('transcript_channel_id')  # ID du salon de transcript
        log_channel_id = config.get('log_channel_id')  # ID du salon de logs
        log_channel = interaction.guild.get_channel(log_channel_id)
        transcript_channel = interaction.guild.get_channel(transcript_channel_id)

        # Créer le dossier de transcription s'il n'existe pas
        os.makedirs('transcripts', exist_ok=True)

        # Récupérer l'utilisateur qui a ouvert le ticket
        user = interaction.user
        
        # Créer l'embed pour le résumé de la fermeture du ticket
        embed = discord.Embed(
            title="Ticket fermé",
            description=f"**Ticket de {user.name}** a été fermé.",
            color=0xffffff  # Couleur blanche
        )
        embed.add_field(name="Ouvert par", value=user.name, inline=True)
        embed.add_field(name="ID du ticket", value=interaction.channel.id, inline=True)
        embed.add_field(name="Date d'ouverture", value=interaction.channel.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.add_field(name="Date de fermeture", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), inline=True)

        # Envoyer le résumé dans le salon de logs
        if log_channel:
            await log_channel.send(embed=embed)

        # Envoyer le résumé à l'utilisateur en message privé
        await user.send(embed=embed)

        # Créer et enregistrer la transcription des messages dans un fichier .txt
        transcript_filename = f"transcripts/by_t4a_{interaction.channel.id}.txt"  # Spécifie le dossier
        messages = []
        async for message in interaction.channel.history(limit=None):
            messages.append(f"{message.created_at.strftime('%Y-%m-%d %H:%M:%S')} - {message.author.name}: {message.content}")
        
        transcript = "\n".join(messages)
        
        # Écrire la transcription dans un fichier
        with open(transcript_filename, "w", encoding='utf-8') as f:
            f.write(transcript)

        # Envoyer la transcription dans le salon de transcript
        if transcript_channel:
            await transcript_channel.send(file=discord.File(transcript_filename))

        # Envoyer le fichier de transcription à l'utilisateur en message privé
        await user.send(file=discord.File(transcript_filename))

        # Supprimer le salon de ticket
        await interaction.channel.delete(reason="Ticket closed")



class Counter(discord.ui.View):
    @discord.ui.button(label='Créer un ticket', style=discord.ButtonStyle.green)
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        global ticket_counts
        ticket_counts += 1

        # Indiquer que l'interaction est reçue et traitée
        await interaction.response.defer(ephemeral=True)
        
        username = interaction.user.name
        channel = await interaction.guild.create_text_channel(username + "-" + str(ticket_counts), category=interaction.channel.category)  # Créer le salon dans la même catégorie
        
        overwrite = discord.PermissionOverwrite()
        overwrite.send_messages = True
        overwrite.read_messages = True
        overwrite.view_channel = True
        
        perms = interaction.channel.overwrites_for(interaction.guild.default_role)
        perms.send_messages = False
        perms.view_channel = False
        
        await channel.set_permissions(interaction.guild.default_role, overwrite=perms)
        await channel.set_permissions(interaction.user, overwrite=overwrite)
        
        embed = discord.Embed(
            title="**Ticket de " + interaction.user.name + "**",
            description="Cliquez sur le bouton ci-dessous pour fermer le ticket.",
            color=discord.Color.green()
        )
        
        await channel.send(embed=embed, view=Close())
        await interaction.followup.send(f"Ticket créé: {channel.mention}", ephemeral=True)

        # Envoi d'un message dans le salon de logs en embed
        with open('config.json') as f:
            config = json.load(f)
        log_channel_id = config.get('log_channel_id')  # ID du salon de logs
        log_channel = interaction.guild.get_channel(log_channel_id)

        if log_channel:
            log_embed = discord.Embed(
                title="**Nouveau Ticket Ouvert**",
                description=f"Un ticket a été ouvert par {interaction.user.mention} dans le salon {channel.mention}.",
                color=0xffffff  # Vous pouvez choisir une autre couleur si nécessaire
            )
            await log_channel.send(embed=log_embed)




async def create_ticket_panel():
    await bot.wait_until_ready()
    channel = bot.get_channel(TICKET_CHANNEL_ID)
    if channel:
        view = Counter()
        embed = discord.Embed(
            title="**" + TICKET_PANEL_NAME + "**",  # Utiliser le nom du panneau chargé
            description="Cliquez sur le bouton ci-dessous pour ouvrir un ticket.",
            color=discord.Color.green()
        )
        await channel.send(view=view, embed=embed)
        print(f"Panel de ticket créé dans {channel.name}")


@bot.command(name="add")
@commands.has_permissions(administrator=True)  # Assurez-vous que seuls les administrateurs peuvent exécuter cette commande
async def add_member(ctx, member: discord.Member):
    """Ajoute un membre et lui donne la permission d'écrire et de voir le salon."""
    with open('config.json') as f:
        config = json.load(f)

    staff_role_id = config['staff']  # Récupérer l'ID du rôle staff
    staff_role = ctx.guild.get_role(staff_role_id)

    if staff_role not in ctx.author.roles:
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande.")
        return

    # Donner les permissions au membre dans le salon actuel
    await ctx.channel.set_permissions(member, read_messages=True, send_messages=True)
    await ctx.send(f"{member.mention} a été ajouté au salon.")

    # Envoi d'un message dans le salon de logs
    logs_channel_id = config.get('logs_channel_id')  # Assurez-vous d'avoir l'ID du salon de logs dans config.json
    logs_channel = bot.get_channel(logs_channel_id)

    if logs_channel:
        embed = discord.Embed(
            title="Membre ajouté au salon",
            description=f"{member.mention} a été ajouté au salon par {ctx.author.mention}.",
            color=0xffffff  # Couleur blanche
        )
        embed.add_field(name="Salon", value=f"[Lien du salon]({ctx.channel.jump_url})", inline=False)
        await logs_channel.send(embed=embed)



OWNER_ROLE_ID = config['owner']  # Assurez-vous que 'owner' est défini dans config.json

@bot.command(name='vide')
@commands.has_role(OWNER_ROLE_ID)  # Vérifie si l'utilisateur a le rôle owner
async def vide(ctx):
    # Spécifiez le dossier où les transcriptions sont stockées
    transcript_folder = "transcripts"  # Changez ceci si nécessaire

    try:
        # Supprimer tous les fichiers dans le dossier de transcription
        for filename in os.listdir(transcript_folder):
            file_path = os.path.join(transcript_folder, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)  # Supprimer le fichier
        await ctx.send("Tous les fichiers de transcription ont été supprimés avec succès.", delete_after=10)
    except Exception as e:
        await ctx.send(f"Une erreur s'est produite lors de la suppression des fichiers: {str(e)}", delete_after=10)




bot.run(config['token'])
