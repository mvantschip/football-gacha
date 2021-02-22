import inspect
import sys

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

consequence_choices = ["m", "k", "b"]


def get_models():
    obj_list = []
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        obj_list.append(obj)
    return obj_list


class DBGuild(models.Model):
    g_id = models.BigIntegerField(verbose_name="Discord ID of the server", primary_key=True)
    name = models.CharField(max_length=256, verbose_name="Discord name of the server")
    time_stamp = models.DateTimeField(verbose_name="Date of adding the guild", default=timezone.now)
    prefix = models.CharField(max_length=512, verbose_name="Prefix for guild", default="!")

    def __repr__(self):
        return f"{self.g_id}:{self.name}"

    def __str__(self):
        return self.__repr__()

    def m_role(self):
        data = [i.role.role_id for i in self.modrole_set.all()]
        return data if len(data) != 0 else None

    def add_m_role(self, role):
        try:
            dbrole = DBRole.objects.get(role_id=role, g=self)
        except DBRole.DoesNotExist:
            dbrole = DBRole(role_id=role, g=self)
            dbrole.save()

        try:
            ModRole.objects.get(g=self, role=dbrole)
        except:
            ModRole(g=self, role=dbrole).save()

    def rm_m_role(self, role):
        try:
            r = ModRole.objects.get(g=self, role__role_id=role)
            r.delete()
        except:
            pass


class ModRole(models.Model):
    g = models.ForeignKey(DBGuild, verbose_name='Guild associated to this mod', on_delete=models.CASCADE)
    role = models.ForeignKey('DBRole', verbose_name="Role that makes user mods", on_delete=models.CASCADE)

    class Meta:
        unique_together = (('g', 'role'))

    def __repr__(self):
        return self.role.__str__()

    def __str__(self):
        return self.__repr__()

class DBUser(models.Model):
    u_id = models.BigIntegerField(verbose_name="Discord id of the user")
    u_name = models.CharField(max_length=64, verbose_name="Discord display name of the user", default="")
    g = models.ForeignKey(DBGuild, verbose_name="Associated server", on_delete=models.CASCADE)
    avatar_url = models.URLField(verbose_name="Avatar url of the account", default=None, null=True)
    is_bot = models.BooleanField(default=False)
    g_admin = models.BooleanField(verbose_name="Admin flag, set by Admin", default=False)
    g_mod = models.BooleanField(verbose_name="Mod flag, set by Admin", default=False)  

    class Meta:
        unique_together = (('u_id', 'g'))

    def __repr__(self):
        return f"{self.u_name}({self.u_id})"

    def __str__(self):
        return self.__repr__()

class DBChannel(models.Model):
    g = models.ForeignKey(DBGuild, verbose_name="Associated server", on_delete=models.CASCADE)
    channel_id = models.BigIntegerField(verbose_name="Discord ID of the channel")
    channel_name = models.CharField(verbose_name="Discord name of the channel", default=None, null=True, max_length=524)

    class Meta:
        unique_together = (('g', 'channel_id'))

    def __repr__(self):
        return f"{self.channel_name}"

    def __str__(self):
        return self.__repr__()


class DBRole(models.Model):
    g = models.ForeignKey(DBGuild, verbose_name="Associated server", on_delete=models.CASCADE)
    position = models.IntegerField(verbose_name="Position on the board", default=None, null=True)
    role_id = models.BigIntegerField(verbose_name="Discord ID of the role")
    role_name = models.CharField(verbose_name="Role name", default=None, null=True, max_length=512)
    role_color_r = models.BigIntegerField(verbose_name="Red part of role color", default=None, null=True)
    role_color_g = models.BigIntegerField(verbose_name="Green part of the role color", default=None, null=True)
    role_color_b = models.BigIntegerField(verbose_name="Blue part of the role color", default=None, null=True)
    base_role = models.BooleanField(verbose_name="Base role for the server", default=False)

    class Meta:
        unique_together = (('g', 'role_id'))

    def __repr__(self):
        return f"{self.role_name}"

    def __str__(self):
        return self.__repr__()


class Cog(models.Model):
    name = models.CharField(max_length=512, verbose_name='Name of the cog', primary_key=True)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.__repr__()


class Command(models.Model):
    name = models.CharField(max_length=512, verbose_name="Name of the command", primary_key=True)
    cog = models.ForeignKey(Cog, verbose_name="Cog this command belongs to", on_delete=models.CASCADE)

    def __repr__(self):
        return f"{self.name} on {self.cog}"

    def __str__(self):
        return self.__repr__()


class CommandStats(models.Model):
    g = models.ForeignKey(DBGuild, verbose_name="Guild that used the command", on_delete=models.SET_NULL, null=True)
    command = models.ForeignKey(Command, verbose_name="Command that was executed", on_delete=models.CASCADE)
    parameters = models.CharField(max_length=2048, verbose_name="Parameters of the command", default=None, null=True)
    timestamp = models.DateTimeField(verbose_name="Timestamp this command was executed", default=timezone.now)
    user = models.ForeignKey(DBUser, verbose_name="User that executed this command", null=True,
                             on_delete=models.CASCADE)

    def __repr__(self):
        return f"{self.g.name}({self.g.id}): {self.command}"

    def __str__(self):
        return self.__repr__()


class GuildStats(models.Model):
    g_joined = models.ForeignKey(DBGuild, verbose_name="Guild that joined the server to their community",
                                 on_delete=models.SET_NULL, null=True, related_name='%(class)s_guild_join')
    g_left = models.ForeignKey(DBGuild, verbose_name="Guild that removed the bot from their server",
                               on_delete=models.SET_NULL, null=True, related_name='%(class)s_guild_leave')
    timestamp = models.DateTimeField(verbose_name="Timestamp this happened", default=timezone.now)
    related_object = models.ForeignKey('self', verbose_name="Related object (i.e. when they joined it)", null=True,
                                       default=None, on_delete=models.SET_NULL)
    count = models.BigIntegerField(verbose_name="Count up or downward")
    total_count = models.BigIntegerField(verbose_name="Total count of guilds the bot is on")

    def __repr__(self):
        if self.g_left is None:
            return f"Added {self.g_joined}: {self.timestamp.strftime('%d.%m.%Y')}"
        else:
            return f"Added {self.g_left}: {self.timestamp.strftime('%d.%m.%Y')}"

    def __str__(self):
        return self.__repr__()


class UserStats(models.Model):
    u = models.ForeignKey(DBUser, verbose_name="User that was added to the bot", on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(verbose_name="Timestamp this happened", default=timezone.now)
    total_count = models.BigIntegerField(verbose_name="Total count of users that are stored in the bot")

    def __repr__(self):
        return f"{self.u}: {self.timestamp.strftime('%d.%m.%Y')} Count {self.total_count}"

    def __str__(self):
        return self.__repr__()


class Error(models.Model):
    g = models.ForeignKey(DBGuild, on_delete=models.CASCADE, verbose_name="Guild where error happened", null=True)
    cmd_string = models.CharField(max_length=2048, verbose_name="Command string that was executed")
    error_type = models.CharField(max_length=256, verbose_name="Error type")
    error = models.CharField(max_length=5000, verbose_name="Error string")
    time_stamp = models.DateTimeField(verbose_name="Time of error.", default=timezone.now)
    traceback = models.CharField(verbose_name="Traceback of error", default=None, null=True, max_length=15000)

    def __repr__(self):
        return f"{self.error} on {self.g.name}"

    def __str__(self):
        return self.__repr__()
