import os
from io import BytesIO

import discord
import numpy as np
import requests
from discord.ext import commands
from PIL import Image

users = {}



def get_imgs(folder):
    # Function that returns a dictionary of the images in a folder
    i = 0
    imgs = {}
    for image_path in os.listdir(folder):
        input_path = os.path.join(folder, image_path)
        imgs[str(i)] = input_path
        i += 1
    return imgs


def resize(folder, size):
    for image_path in os.listdir(folder):
        input_path = os.path.join(folder, image_path)
        image = Image.open(input_path)
        image.thumbnail((size, size), Image.ANTIALIAS)
        image.save(input_path)

def check_hat(args):
    """Helper function that handles hat manipulations, like flip and scale"""
    try:
        folder = get_imgs("crimmis_hats/")
        hat = Image.open(folder.get("0"))
        for arg in args:
            if arg.startswith("type="):
                value = arg.split("=")[1]
                hat = Image.open(folder.get(value))

        w_offset, h_offset = 150, 0
        hat_width, hat_height = 350, 300
        for arg in args:
            if arg == "flip":
                hat = hat.transpose(Image.FLIP_LEFT_RIGHT)
                w_offset, h_offset = 0, 0
            if arg.startswith("scale="):
                value = float(arg.split("=")[1])
                hat_width, hat_height = int(hat.width * value), int(hat.height * value)

        hat = hat.resize((hat_width, hat_height))
    except:
        return None, None, None

    return hat, w_offset, h_offset


def move(args, width, height):
    """Helper function used to shift the hat in a certain direction"""
    for arg in args:
        if arg.startswith("left="):
            value = arg.split("=")[1]
            width -= int(value)
        if arg.startswith("right="):
            value = arg.split("=")[1]
            width += int(value)
        if arg.startswith("up="):
            value = arg.split("=")[1]
            height -= int(value)
        if arg.startswith("down="):
            value = arg.split("=")[1]
            height += int(value)
    return width, height



class Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.id in users:
            users.pop(message.author.id, None)

    @commands.command(pass_context=True)
    async def hathelp(self, ctx):
        if isinstance(ctx.message.channel, discord.DMChannel):
            print("Help message used for {} in DM".format(ctx.message.author.name))
        else:
            print("Help message used in {}".format(ctx.message.channel.guild.name))

        string = (
            "To use: **!hat**\n"
            "To see available hats: **!hats**\n"
            "\n"
            "Parameters (commands use the format **command=number**):\n"
            "type (0-4) - chooses what type of hat to use\n"
            "flip - flips the image horizontally\n"
            "scale - scales the image to a different size\n"
            "left/right/up/down - moves the hat in the given direction\n"
            "\n"
            "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ \n"
            "**Example of use with parameters: '!hat type=2 scale=2 up=20 left=50'**\n"
            "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ \n"
            "\n"
            "This command selects hat 2, scales it to 2x size, and moves it accordingly\n"
            "\n"
            "Note on image quality: higher resolution avatars results in cleaner images\n"
        )

        embed = discord.Embed()
        embed.add_field(name="CrimmisHatBot Usage!", value=string)
        await ctx.channel.send(embed=embed)

    @commands.command(pass_context=True)
    async def hats(self, ctx):
        print("Showing available hats in {}".format(ctx.message.channel.guild.name))
        await ctx.channel.send(
            "Here are all the available hats!", file=discord.File("crimmis_hats/hats.png")
        )


    @commands.command(pass_context=True)
    async def hat(self, ctx, *args):
        """Handles creating and returning a hat to a user"""
        try:
            # Check for direct message
            if isinstance(ctx.message.channel, discord.DMChannel):
                print(
                    "Making hat for {} in DM \t Arguments: {}".format(
                        ctx.message.author, args
                    )
                )
            else:
                print(
                    "Making hat for {} in {} \t Arguments: {}".format(
                        ctx.message.author, ctx.message.channel.guild.name, args
                    )
                )
            message = ctx.message

            # Check whether an attachment is provided
            if len(message.attachments) > 0:
                url = message.attachments[0].url
            else:
                url = ctx.message.author.avatar.url

            # Get the image via an html request
            response = requests.get(url, headers={"User-agent": "Mozilla/5.0"})
            iamge_message_id = Image.open(BytesIO(response.content)).resize((500, 500))

            # Apply base transformations as needed (flip and scale)
            hat, width, height = check_hat(args)
            if hat is None:
                await ctx.channel.send("Wrong command formatting, try again!")
                return

            # Apply move given and temporarily save hat
            iamge_message_id.paste(hat, move(args, width, height), mask=hat)
            file_loc = BytesIO()
            iamge_message_id.save(file_loc, format="PNG")
            file_loc.seek(0)

            # Check whether previous hat already exists and clean it up
            if message.author.id in users.keys() and not isinstance(
                ctx.message.channel, discord.DMChannel
            ):
                try:
                    await ctx.channel.delete_messages([users.get(message.author.id)])
                except discord.errors.NotFound:
                    print(
                        "Could not delete message for {} - {}".format(
                            message.author.name, message.author.name
                        )
                    )

            # Send finalized image
            iamge_message_id = await ctx.channel.send(
                "Here is your hat, {}!".format(ctx.message.author.mention),
                file=discord.File(file_loc, filename=f"{ctx.message.author.name}.png"),
            )

            # Add current message to the users dictionary
            users[message.author.id] = iamge_message_id

            # try to delete the original message if we have the permission
            try:
                await ctx.message.delete()
            except discord.errors.Forbidden:
                print("Could not delete message for {} - {}".format(message.author.name, message.author.name))

        except Exception as e:
            # Catching general exceptions to give to users, handles traceback print out still
            print(
                "Error making hat for {}, args {}. Exception {}.".format(
                    ctx.message.author, args, e
                )
            )
            await ctx.channel.send(
                "{}, an error has occurred when making the hat. Make sure the arguments are correct!".format(
                    ctx.message.author.name
                )
            )


async def setup(client):
    await client.add_cog(Cog(client))