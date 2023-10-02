from redbot.core import commands, Config
import random
import re
import discord

class Arbitrarylist(commands.Cog):



    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=54736)  # Use your own unique identifier
        self.config.register_guild(lists={})
    
    
    async def able_to_view(self,user,list):
        return (list["creator_id"] == user.id
            or user.guild_permissions.administrator
            or f"<@{str(user.id)}>" in list.get("allowed_users", [])
            or list["hidden"] == False
        )

    async def able_to_edit(self,user,list): 
        return (list["creator_id"] == user.id
            or user.guild_permissions.administrator
            or f"<@{str(user.id)}>" in list.get("allowed_users", [])
            or list["locked"] == False
        )
    
    async def no_view_perms_msg(self,ctx,list_name):
        await ctx.send(f"The list **{list_name}** is hidden from you.")

    async def no_edit_perms_msg(self,ctx,list_name):
        await ctx.send(f"You are not authorized to edit the list **{list_name}**.")
    
    async def no_list_exists_msg(self,ctx,list_name):
        await ctx.send(f"List **{list_name}** not found. Use `;al help` to view valid commands.")


    @commands.group(name="al",invoke_without_command=True)
  
    async def al(self, ctx, list_name:str, page_num:int = 1):
        """
        Returns a list of a given name.

        Parameters
        ----------
        list_name : The name of the list you want to view.
        page_num : (Optional) the page number of the list. Defaults to 1.
    
        """
        if ctx.invoked_subcommand is None:
            lists = await self.config.guild(ctx.guild).lists()
            if list_name in lists:
                list = lists[list_name]
                if await self.able_to_view(user=ctx.author, list=list):
                    items = lists[list_name]["items"]
                    if items:
                        try:
                            page = 1
                            page_size = 0
                            max_page_size = 3000
                            list_display = []
                            
                            things = []

                            for i, item in enumerate(items):
                                item_length = len(item)
                                if page_size + item_length < max_page_size and i < page * 25:
                                    list_display.append(f"{i + 1}. {item}")
                                    page_size += item_length
                                else:
                                    # Create a new page
                                    things.append("\n".join(list_display))

                                    # Reset page variables for the new page
                                    list_display = [f"{i + 1}. {item}"]
                                    page_size = item_length
                                    page += 1

                            # Send the last page if there are remaining items
                            if list_display:
                                things.append("\n".join(list_display))
                                page += 1

                            if page_num < 1:
                                page_num = 1
                            if page_num > len(things):
                                page_num = len(things)

                            # Get the top role of the member
                            creator_id = lists[list_name]["creator_id"]
                            user = ctx.guild.get_member(int(creator_id))
                            role_color = discord.Color.default()
                            if user:
                                top_role =  user.top_role
                            # Get the color of the top role
                            role_color = top_role.color if top_role else discord.Color.default()
                            
                            embed = discord.Embed(
                                    title=f"{list_name} (Page {page_num}/{len(things)})",
                                    color=role_color
                                )
                            embed.description = things[page_num-1]

                            await ctx.send(embed=embed)

                        except ValueError:
                            await ctx.send("Invalid page number.")
                    else:
                        await ctx.send(f"The list **{list_name}** is empty.")

                else:
                    await self.no_view_perms_msg(ctx=ctx,list_name=list_name)
            else:
                await self.no_list_exists_msg(ctx=ctx,list_name=list_name)
      
                        
    @al.command(name="new")
    async def create_list(self, ctx, list_name:str, *, items:str=None):
        """
        Create a new List.

        Parameters
        ----------
        list_name : The name of the list.
        items : (Optional) The initial items to add to the list. Seperate items with `^`.
    
        """
        lists = await self.config.guild(ctx.guild).lists()
        if list_name in lists:
            await(ctx.send(f"A list with the name **{list_name}** already exists"))
            return
        
        all_command_names =  ["new","add","remove","allow","disallow","lock","unlock","delete","search","info","roll","show","hide", "transfer", "mylist"]
        if list_name in all_command_names:
            await ctx.send(f"You cannot create a list with the same name as a command or subcommand.")
            return
        
        if len(list_name) > 50:
            await ctx.send("List name too long. What are you trying to do, kill me?")
            return
        

        
        lists[list_name] = {
            "items": [],
            "creator_id": ctx.author.id,
            "locked": False,
            "hidden": False,
            "allowed_users": [],
        }
        if items:
            item_list = items.split('^') if items.strip() else []
            lists[list_name]["items"].extend(item_list)
        await self.config.guild(ctx.guild).lists.set(lists)
        if items:
            await ctx.send(f"Created a new list **{list_name}** with items: {', '.join(item_list)}"[0:1990])
        else:
            await ctx.send(f"Created a new empty list **{list_name}**.")


    @al.command(name="add")
    async def add_to_list(self, ctx, list_name:str, *, items:str):
        """
        Add items to an existing List.

        Parameters
        ----------
        list_name : The name of the list you want to add to.
        items : The initial items to add to the list. Seperate items with `^`.
    
        """
        lists = await self.config.guild(ctx.guild).lists()
        if list_name in lists:
            list = lists[list_name]
            if not(await self.able_to_view(user=ctx.author,list=list) and await self.able_to_edit(user=ctx.author,list=list)):
                await self.no_edit_perms_msg(ctx=ctx,list_name=list_name)
                return
            
            # Split the items into a list using '^' delimiter
            items_list = items.split('^')

            # Remove empty items from the list
            items_list = [item.strip() for item in items_list if item.strip()]

            lists[list_name]["items"].extend(items_list)
            await self.config.guild(ctx.guild).lists.set(lists)
            await ctx.send(f"Added items to **{list_name}**")

        else:
            await self.no_list_exists_msg(ctx=ctx,list_name=list_name)


    @al.command(name="remove")
    async def remove_from_list(self, ctx, list_name:str, *, indices:str):
        """
        Add items to an existing List.

        Parameters
        ----------
        list_name : The name of the list you want to add to.
        items : The item numbers to remove.
    
        """
        lists = await self.config.guild(ctx.guild).lists()
        if list_name in lists:
            list = lists[list_name]
            if not(await self.able_to_view(user=ctx.author,list=list) and await self.able_to_edit(user=ctx.author,list=list)):
                await self.no_edit_perms_msg(ctx=ctx,list_name=list_name)
                return
            try:
                indices = [int(index) for index in indices.split()]
                indices.sort(reverse=True)
                removed_items = []
                for index in indices:
                    if 1 <= index <= len(lists[list_name]["items"]):  # Adjusted index range to base-1
                        removed_items.append(lists[list_name]["items"].pop(index - 1))
                await self.config.guild(ctx.guild).lists.set(lists)
                if removed_items:
                    await ctx.send(f"Removed items from **{list_name}**: {', '.join(removed_items)}"[0:1990])
                else:
                    await ctx.send(f"Couln't remove items {indices} from **{list_name}**")
            except ValueError:
                await ctx.send("Invalid item numbers.")
        else:
            await self.no_list_exists_msg(ctx=ctx,list_name=list_name)


    @al.command(name="delete")    
    async def delete_list(self, ctx, list_name):
        """
        Deletes a list.

        Parameters
        ----------
        list_name : The name of the list you want to delete.
    
        """
        lists = await self.config.guild(ctx.guild).lists()
        if list_name in lists:
            list = lists[list_name]
            if not(await self.able_to_view(user=ctx.author,list=list) and await self.able_to_edit(user=ctx.author,list=list)):
                await self.no_edit_perms_msg(ctx=ctx,list_name=list_name)
                return
            del lists[list_name]
            await self.config.guild(ctx.guild).lists.set(lists)
            await ctx.send(f"Deleted list **{list_name}**.")
 
        else:
            await self.no_list_exists_msg(ctx=ctx,list_name=list_name)

    @al.command(name="info")  
    async def info_list(self, ctx, list_name):
        """
        Views info about a list.

        Parameters
        ----------
        list_name : The name of the list you want to view the info of.
    
        """
        lists = await self.config.guild(ctx.guild).lists()
        if list_name in lists:

            num_pages = 0

            items = lists[list_name]["items"]
            if items:

                page = 1
                page_size = 0
                max_page_size = 3000
                list_display = []
                

                for i, item in enumerate(items):
                    item_length = len(item)
                    if page_size + item_length < max_page_size and i < page * 25:
                        list_display.append(f"{i + 1}. {item}")
                        page_size += item_length
                    else:
                        # Create a new page
                        num_pages += 1

                        # Reset page variables for the new page
                        list_display = [f"{i + 1}. {item}"]
                        page_size = item_length
                        page += 1

                # Send the last page if there are remaining items
                if list_display:
                    num_pages += 1
                    page += 1

            list_data = lists[list_name]
            items = list_data["items"]
            num_items = len(items)
            creator_id = list_data["creator_id"]
            creator = ctx.guild.get_member(int(creator_id))
            creator_name = creator.display_name if creator else "Unknown"

            locked = list_data["locked"]
            hidden = list_data["hidden"]
            allowed_users = list_data.get("allowed_users", [])

            # Get the top role of the member
            top_role = ctx.author.top_role
            # Get the color of the top role
            role_color = top_role.color if top_role else discord.Color.default()
            embed = discord.Embed(title=f"List Information: {list_name}", color = role_color)
            embed.add_field(name="Number of Items", value=num_items, inline=True)
            embed.add_field(name="Number of Pages", value=num_pages, inline=True)
            embed.add_field(name="Owner", value=creator_name, inline=True)
            embed.add_field(name="Locked", value='Yes' if locked else 'No', inline=True)
            embed.add_field(name="Hidden", value='Yes' if hidden else 'No', inline=True)

            if allowed_users:
                allowed_users_mentions = [f"{user_id}" for user_id in allowed_users]
                embed.add_field(name="Allowed Users", value=', '.join(allowed_users_mentions)[:1000], inline=False)

            await ctx.send(embed=embed)
        else:
            await self.no_list_exists_msg(ctx=ctx,list_name=list_name)


    @al.command(name="lock") 
    async def lock_list(self, ctx, list_name):
        """
        Locks a list, preventing users from editing it.

        Parameters
        ----------
        list_name : The name of the list you want to lock.
    
        """
        lists = await self.config.guild(ctx.guild).lists()
        if list_name in lists:
            list = lists[list_name]
            if not(await self.able_to_view(user=ctx.author,list=list) and await self.able_to_edit(user=ctx.author,list=list)):
                await self.no_edit_perms_msg(ctx=ctx,list_name=list_name)
                return
            
            lists[list_name]["locked"] = True
            await self.config.guild(ctx.guild).lists.set(lists)
            await ctx.send(f"List **{list_name}** has been locked. Only allowed users and the owner can edit it.")
        else:
           await self.no_list_exists_msg(ctx=ctx,list_name=list_name)

    @al.command(name="unlock") 
    async def unlock_list(self, ctx, list_name):
        """
        Unlocks a list, allowing users to edit it.

        Parameters
        ----------
        list_name : The name of the list you want to unlock.
    
        """
        lists = await self.config.guild(ctx.guild).lists()
        if list_name in lists:
            list = lists[list_name]
            if not(await self.able_to_view(user=ctx.author,list=list) and await self.able_to_edit(user=ctx.author,list=list)):
                await self.no_edit_perms_msg(ctx=ctx,list_name=list_name)
                return
            
            lists[list_name]["locked"] = False
            await self.config.guild(ctx.guild).lists.set(lists)
            await ctx.send(f"List **{list_name}** has been unlocked. Any user can edit it.")
        else:
           await self.no_list_exists_msg(ctx=ctx,list_name=list_name)

    @al.command(name="hide") 
    async def hide_list(self, ctx, list_name):
        """
        Hieds a list, blocking users from being able to view/edit it.

        Parameters
        ----------
        list_name : The name of the list you want to hide.
    
        """
        lists = await self.config.guild(ctx.guild).lists()
        if list_name in lists:
            list = lists[list_name]
            if not(await self.able_to_view(user=ctx.author,list=list) and await self.able_to_edit(user=ctx.author,list=list)):
                await self.no_edit_perms_msg(ctx=ctx,list_name=list_name)
                return
            
            lists[list_name]["hidden"] = True
            await self.config.guild(ctx.guild).lists.set(lists)
            await ctx.send(f"List **{list_name}** has been hidden. Only allowed users and the owner can view/edit it.")
        else:
           await self.no_list_exists_msg(ctx=ctx,list_name=list_name)

    @al.command(name="show") 
    async def show_list(self, ctx, list_name):
        """
        Shows a list, allowing users to be able to view it.

        Parameters
        ----------
        list_name : The name of the list you want to show.
    
        """
        lists = await self.config.guild(ctx.guild).lists()
        if list_name in lists:
            list = lists[list_name]
            if not(await self.able_to_view(user=ctx.author,list=list) and await self.able_to_edit(user=ctx.author,list=list)):
                await self.no_edit_perms_msg(ctx=ctx,list_name=list_name)
                return
            
            lists[list_name]["hidden"] = False
            await self.config.guild(ctx.guild).lists.set(lists)
            await ctx.send(f"List **{list_name}** has been shown. Any user can view it.")
        else:
           await self.no_list_exists_msg(ctx=ctx,list_name=list_name)

    @al.command(name="roll") 
    async def roll_from_list(self, ctx, list_name):
        """
        Rolls a random it from a list.

        Parameters
        ----------
        list_name : The name of the list you want to roll from.
    
        """
        lists = await self.config.guild(ctx.guild).lists()
        if list_name in lists:
            if not(await self.able_to_view(user=ctx.author,list=list)):
                await self.no_view_perms_msg(ctx=ctx,list_name=list_name)
                return
            
            items = lists[list_name]["items"]
            if items:
                rolled_item = random.choice(items)
                await ctx.send(f"Rolled:\n {rolled_item[:1900]}")
            else:
                await ctx.send(f"The list **{list_name}** is empty.")
        else:
            await self.no_list_exists_msg(ctx=ctx,list_name=list_name)

    @al.command(name="allow") 
    async def allow_user_to_edit_list(self, ctx, list_name, user):
        """
        Add user to the list of allowed users so they can view/edit locked/hidden lists.

        Parameters
        ----------
        list_name : The name of the list you want allow them for.
        uder_id : The user you wish to allow.
    
        """
        user_arg = user
        lists = await self.config.guild(ctx.guild).lists()
        if list_name in lists:
            list = lists[list_name]
            if not(await self.able_to_view(user=ctx.author,list=list) and await self.able_to_edit(user=ctx.author,list=list)):
                await self.no_edit_perms_msg(ctx=ctx,list_name=list_name)
                return
            # Use regular expression to validate and extract the user ID from the mention
            if user_arg.isdigit():
                user_arg = f"<@{user_arg}>"

            mention_pattern = re.compile(r"<@(\d+)>")
            match = mention_pattern.match(user_arg)
            if match and ctx.guild.get_member(int(match.group(1))):
                user_id = user_arg
                if str(user_id) not in lists[list_name]["allowed_users"]:
                    lists[list_name]["allowed_users"].append(str(user_id))
                    await self.config.guild(ctx.guild).lists.set(lists)
                    await ctx.send(f"Added user **{ctx.guild.get_member(int(match.group(1))).display_name}** to the allowed users of **{list_name}**.")
                else:
                    await ctx.send(f"User **{ctx.guild.get_member(int(match.group(1))).display_name}** is already allowed to edit **{list_name}**.")
            else:
                await ctx.send("User not found.")
        else:
            await self.no_list_exists_msg(ctx=ctx,list_name=list_name)

    @al.command(name="disallow")
    async def block_user_from_editing_list(self, ctx, list_name, user):
        """
        Remove user to the list of allowed users so they can't view/edit locked/hidden lists.

        Parameters
        ----------
        list_name : The name of the list you want disallow them for.
        uder_id : The user you wish to disallow.
    
        """
        user_arg = user
        lists = await self.config.guild(ctx.guild).lists()
        if list_name in lists:
            if not(await self.able_to_view(user=ctx.author,list=list) and await self.able_to_edit(user=ctx.author,list=list)):
                await self.no_edit_perms_msg(ctx=ctx,list_name=list_name)
                return

            # Use regular expression to validate and extract the user ID from the mention
            if user_arg.isdigit():
                user_arg = f"<@{user_arg}>"

            mention_pattern = re.compile(r"<@(\d+)>")
            match = mention_pattern.match(user_arg)
            if match and ctx.guild.get_member(int(match.group(1))):
                user_id = user_arg

                if str(user_id) in lists[list_name]["allowed_users"]:
                    lists[list_name]["allowed_users"].remove(str(user_id))
                    await self.config.guild(ctx.guild).lists.set(lists)
                    await ctx.send(f"Removed user **{ctx.guild.get_member(int(match.group(1))).display_name}** from the allowed users of **{list_name}**.")
                else:
                    await ctx.send(f"User **{ctx.guild.get_member(int(match.group(1))).display_name}** is not in the allowed users list of **{list_name}**.")
            else:
                await ctx.send("User not found.")
        else:
            await self.no_list_exists_msg(ctx=ctx,list_name=list_name)

    @al.command(name="search")
    async def search_lists(self, ctx, keyword,page_num:int=1):
        """
        Search for existing lists using a keyword.

        Parameters
        ----------
        keyword : keyword to search for.
        dispage : (Optional) the page number of search results you wish to view.
    
        """
        dispPage = page_num
        lists = await self.config.guild(ctx.guild).lists()
        matching_lists = [(list_name, list_data) for list_name, list_data in lists.items() if keyword in list_name]

        if matching_lists:
            max_page_size = 1000  # Maximum characters allowed in an embed
            current_characters = 0

            things = []
            page = 1
            page_size = 0
            list_display = []
           
            for list_name, list_data in matching_lists:
                creator_id = list_data["creator_id"]
                creator = ctx.guild.get_member(int(creator_id))
                creator_name = creator.display_name if creator else "Unknown"
                num_entries = len(list_data["items"])
                field_text = f"Owner: {creator_name} Entries: {num_entries}"
                item = f"{list_name} - {field_text}"
                item_length = len(item)
                if page_size + item_length < max_page_size:
                    list_display.append(f"{item}")
                    page_size += item_length
                else:
                    # Create a new page
                    things.append("\n".join(list_display))

                    # Reset page variables for the new page
                    list_display = [f"{item}"]
                    page_size = item_length
                    page += 1
                

                # Send the last page if there are remaining items
            if list_display:
                things.append("\n".join(list_display))
                page += 1

            if dispPage < 1:
                dispPage = 1
            if dispPage > len(things):
                dispPage = len(things)

            # Get the top role of the member
            top_role = ctx.author.top_role
            # Get the color of the top role
            role_color = top_role.color if top_role else discord.Color.default()
            embed = discord.Embed(
                title=f"Lists with '{keyword}' in their names (Page {dispPage}/{len(things)})",
                color=role_color)
            embed.description = things[dispPage-1]

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"No lists found matching \"{keyword}\".")

    @al.command(name="mylists")
    async def my_lists(self, ctx, page_num:int=1):
        """
        Search for existing lists you created.
        """
        dispPage = page_num
        user_id = ctx.author.id
        lists = await self.config.guild(ctx.guild).lists()
        matching_lists = [(list_name, list_data) for list_name, list_data in lists.items() if lists[list_name]["creator_id"] == user_id]

        if matching_lists:
            max_page_size = 1000  # Maximum characters allowed in an embed
            current_characters = 0

            things = []
            page = 1
            page_size = 0
            list_display = []
           
            for list_name, list_data in matching_lists:
                creator_id = list_data["creator_id"]
                creator = ctx.guild.get_member(int(creator_id))
                creator_name = creator.display_name if creator else "Unknown"
                num_entries = len(list_data["items"])
                field_text = f"Entries: {num_entries}"
                item = f"{list_name} - {field_text}"
                item_length = len(item)
                if page_size + item_length < max_page_size:
                    list_display.append(f"{item}")
                    page_size += item_length
                else:
                    # Create a new page
                    things.append("\n".join(list_display))

                    # Reset page variables for the new page
                    list_display = [f"{item}"]
                    page_size = item_length
                    page += 1
                

                # Send the last page if there are remaining items
            if list_display:
                things.append("\n".join(list_display))
                page += 1

            if dispPage < 1:
                dispPage = 1
            if dispPage > len(things):
                dispPage = len(things)
                
            # Get the top role of the member
            top_role = ctx.author.top_role
            # Get the color of the top role
            role_color = top_role.color if top_role else discord.Color.default()
            embed = discord.Embed(
                title=f"Lists owned by {ctx.guild.get_member(int(user_id)).display_name} (Page {dispPage}/{len(things)})",
                color=role_color
            )
            embed.description = things[dispPage-1]

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"No lists found made by **{ctx.guild.get_member(int(user_id)).display_name}**.")

    @al.command(name="transfer")
    async def transfer_ownership(self, ctx, list_name, new_owner):
        """Transfer ownership of a list to a new user (creator/admin only)"""
        lists = await self.config.guild(ctx.guild).lists()
        if list_name in lists:
            current_owner_id = lists[list_name]["creator_id"]
            if (
                current_owner_id == ctx.author.id
                or ctx.author.guild_permissions.administrator
            ):
                # Use regular expression to validate and extract the user ID from the mention
                if new_owner.isdigit():
                    new_owner = f"<@{new_owner}>"
                mention_pattern = re.compile(r"<@(\d+)>")
                match = mention_pattern.match(new_owner_arg)
                if match and ctx.guild.get_member(int(match.group(1))):
                    new_owner_id = int(match.group(1))
                    new_owner = ctx.guild.get_member(new_owner_id)
                    if new_owner:
                        lists[list_name]["creator_id"] = new_owner.id
                        await self.config.guild(ctx.guild).lists.set(lists)
                        await ctx.send(f"Ownership of list **{list_name}** has been transferred to {new_owner.mention}.")
                    else:
                        await ctx.send("User not found.")
                else:
                    await ctx.send("User not found.")
            else:
                await ctx.send(f"You are not authorized to transfer ownership of the list **{list_name}**.")
        else:
            await self.no_list_exists_msg(ctx=ctx,list_name=list_name)

    @al.command(name="help") 

    async def display_help(self, ctx):
        """
        Display list of commands
        """
        # Get the top role of the member
        top_role = ctx.author.top_role
        # Get the color of the top role
        role_color = top_role.color if top_role else discord.Color.default()
        help_embed = discord.Embed(
            title="Arbitrary Lists Help",
            description="Use `;al command` to interact with arbitrary lists:",
            color=role_color
        )

        help_embed.add_field(
            name="`listName`",
            value="Display contents of the list.",
            inline=False
        )

        help_embed.add_field(
            name="`listName` `pageNum`",
            value="Display contents the given page for a list.",
            inline=False
        )

        help_embed.add_field(
            name="**new** `listName` `item` `...`",
            value="Create a new list with the specified name and items. Items are separated with `^`.",
            inline=False
        )

        help_embed.add_field(
            name="**add** `listName` `item` `...`",
            value="Add items to an existing list. Items are separated with `^`.",
            inline=False
        )

        help_embed.add_field(
            name="**remove** `listName` `item number` `...`",
            value="Remove items from an existing list.",
            inline=False
        )

        help_embed.add_field(
            name="**search** `keyword` `pagenum`",
            value="Search for lists by keyword in their names. Optionally specify a page number",
            inline=False
        )

        help_embed.add_field(
            name="**delete** `listName`",
            value="Delete an existing list.",
            inline=False
        )

        help_embed.add_field(
            name="**lock** `listName`",
            value="Lock a list (only the creator & allowed users can edit it).",
            inline=False
        )

        help_embed.add_field(
            name="**unlock** `listName`",
            value="Unlock a list (any user can edit it).",
            inline=False
        )

        help_embed.add_field(
            name="**hide** `listName`",
            value="Hide a list (only the creator & allowed users can view it).",
            inline=False
        )

        help_embed.add_field(
            name="**show** `listName`",
            value="Show a list (any user can view it).",
            inline=False
        )

        help_embed.add_field(
            name="**allow** `listName` `userID`",
            value="Allow a user to edit a locked list or view a hidden list.",
            inline=False
        )

        help_embed.add_field(
            name="**disallow** `listName` `userID`",
            value="Remove user from allowed editing a locked list or viewing a hidden list.",
            inline=False
        )

        help_embed.add_field(
            name="**transfer** `listName` `userID`",
            value="Give ownership of one of your lists to another user.",
            inline=False
        )

        help_embed.add_field(
            name="**mylists** 'pagenum`",
            value="Search for lists you own. Optionally specify a page number",
            inline=False
        )

        help_embed.add_field(
            name="**roll** `listName`",
            value="Roll a random item from a list.",
            inline=False
        )
        help_embed.add_field(
            name="**info** `listName`",
            value="Display info about a list.",
            inline=False
        )

        await ctx.send(embed=help_embed)
    