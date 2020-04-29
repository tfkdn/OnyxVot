import discord
from discord.ext import commands, tasks
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os
import re
from .info import timeStringHandler
from typing import Optional


async def is_owner(ctx):
    return ctx.author.id == 242094224672161794


ap = os.path.abspath(__file__)
ap = ap[:len(ap) - 11]

engine = create_engine(f"sqlite:///{ap}db_files/rem.db", echo=False)

Base = declarative_base()


class Reminder(Base):
    __tablename__ = "Reminders"

    rem_id = Column(Integer(), primary_key=True)
    desc = Column(String(100))
    time_due_col = Column(DateTime)
    user_bind = Column(Integer())

    def __repr__(self):
        due = self.time_due_col - datetime.datetime.now()
        due = timeStringHandler(due)
        str_due = f"{due[0]}:{due[1]}:{due[2]}"
        return f"{self.rem_id}. {self.desc} due in {str_due}"

    def __str__(self):
        due = self.time_due_col - datetime.datetime.now()
        due = timeStringHandler(due)
        str_due = f"{due[0]}:{due[1]}:{due[2]}"
        return f"{self.desc} due in {str_due}"


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine, expire_on_commit=False)
session = Session()


def get_datetime_obj(st: str) -> datetime.timedelta:
    res = datetime.timedelta()  # Initializes res

    dig = re.split(r"\D+", st)  # Splits on non digits
    dig = [e for e in dig if e != ""]  # Removes empties

    chars = re.split(r"\d+", st)  # Splits on digits
    chars = [e for e in chars if e != ""]  # Removes empties

    if " " in chars or " " in dig:
        raise Exception("Don't use spaces in the input")

    dic = dict(zip(chars, dig))  # Creates a dic unit : amount

    for val in dic:
        if val == "m":
            res += datetime.timedelta(minutes=int(dic[val]))
        if val == "h":
            res += datetime.timedelta(hours=int(dic[val]))
        if val == "d":
            res += datetime.timedelta(days=int(dic[val]))

    return res  # Returns added Timedelta


class ReminderCog(commands.Cog, name="ReminderCog"):

    def __init__(self, bot):
        self.bot = bot
        ct = datetime.datetime.now()
        self.ct = ct - datetime.timedelta(microseconds=ct.microsecond)
        self.time_updater.start()
        self.db_pruner.start()

    @tasks.loop(seconds=1)
    async def time_updater(self):
        ct = datetime.datetime.now()
        self.ct = ct - datetime.timedelta(microseconds=ct.microsecond)

        rems_test = [remind for remind in session.query(Reminder).filter(Reminder.time_due_col == self.ct)]

        if len(rems_test) != 0:
            user = self.bot.get_user(rems_test[0].user_bind)
            await user.send(f"**Reminder: **{rems_test[0].desc}")

            session.delete(rems_test[0])
            session.commit()
            session.close()

    @tasks.loop(hours=12)
    async def db_pruner(self):

        exp_reminders = [remind for remind in session.query(Reminder).filter(Reminder.time_due_col < self.ct)]

        for r in exp_reminders:
            session.delete(r)

        session.commit()
        session.close()

    @commands.command(aliases=["t", "ct"])
    async def current_time(self, ctx):
        await ctx.channel.send(f"{self.ct}")

    @commands.group(name="r", invoke_without_command=True)
    async def rem(self, ctx, *args):
        e = discord.Embed(title="Reminder Module:",
                          description="Commands supported: \n"
                                      "1.`list : Lists all your reminders `\n"
                                      "2.`me : [description] in [time]`\n"
                                      "3.`prune : [reminder id as shown in list]`(WIP- Owner only)\n"
                                      "4.`prune_user : [user_id]` (Owner Only)",
                          colour=1741991)

        await ctx.send(embed=e)

    @rem.command(aliases=["ls"])
    async def list(self, ctx, user_id: Optional[str]):

        if user_id is None:
            at = ctx.author.id
        elif (user_id is not None) and await is_owner(ctx) and (user_id != "all"):
            at = int(user_id)

        query = session.query(Reminder)

        rems_list = [remind for remind in query.filter(Reminder.user_bind == at).order_by(Reminder.time_due_col)]

        if user_id == "all" and await is_owner(ctx):
            rems_list = [remind for remind in query.order_by(Reminder.time_due_col)]

        if len(rems_list) != 0:

            res_str = ""
            for r in rems_list:
                res_str += str(r.rem_id) + ". " + str(r)
                res_str += "\n"

            e = discord.Embed(title="Reminders:",
                              description=res_str,
                              colour=1741991)

        else:
            e = discord.Embed(title="No Reminders Present :)", colour=1741991)

        e.set_footer(icon_url=str(self.bot.get_user(at).avatar_url),
                     text=f"Reminders for {self.bot.get_user(at).name}")

        await ctx.channel.send(embed=e)

    @rem.command()
    async def me(self, ctx, rem_dsc, junk_in, str_time_due):

        if junk_in != "in":
            rem_dsc = junk_in

        time_due = self.ct + get_datetime_obj(str_time_due)
        r = Reminder(desc=rem_dsc, time_due_col=time_due, user_bind=ctx.author.id)
        session.add(r)

        e = discord.Embed(title="Added:",
                          description=r.__str__(),
                          colour=1741991)

        await ctx.channel.send(embed=e)

        session.commit()
        session.close()

    @rem.command()
    @commands.check(is_owner)
    async def prune(self, ctx, id_num):

        # TODO: make the prune command only work for users rems

        rem_prune = session.query(Reminder).filter(Reminder.rem_id == id_num).first()

        e = discord.Embed(title="Deleted:", description=str(rem_prune), colour=1741991)

        session.delete(rem_prune)
        session.commit()
        session.close()

        await ctx.channel.send(embed=e)

    @rem.command()
    @commands.check(is_owner)
    async def prune_user(self, ctx, id_num):

        user_to_rem = self.bot.get_user(id_num)

        rem_prune = [rem for rem in session.query(Reminder).filter(Reminder.user_bind == user_to_rem)]

        desc_deletion = ""

        for rem in rem_prune:
            desc_deletion += str(rem.rem_id) + ". " + str(rem)
            desc_deletion += "\n"
            session.delete(rem)

        e = discord.Embed(title="Deleted:", description=str(desc_deletion), colour=1741991)

        session.commit()
        session.close()

        await ctx.channel.send(embed=e)

    #  TODO: add a filter to user input on reminders
    #  TODO: Allow prune for a users own rems
    #  TODO: Make list be able to deal with more than 2500 reminders


def setup(bot):
    bot.add_cog(ReminderCog(bot))
    print("ReminderCog has been loaded")
