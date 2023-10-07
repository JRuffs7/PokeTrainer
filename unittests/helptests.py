import unittest

from services import helpservice


class HelpTests(unittest.TestCase):

  def test_invalid_admin(self):
    (valid, description) = helpservice.BuildCommandHelp("start", False)
    self.assertEqual(False, valid, "Admin only command returned for non-admin")
    self.assertEqual("", description,
                     "Admin only command returned for non-admin")

  def test_invalid_command(self):
    (valid, description) = helpservice.BuildCommandHelp("sleep", True)
    self.assertEqual(False, valid, "Non-existent command returned")
    self.assertEqual("", description, "Non-existent command returned")

  def test_valid_admin(self):
    (valid, description) = helpservice.BuildCommandHelp("getserver", True)
    self.assertEqual(True, valid,
                     "Command not returned when it should have been valid")
    self.assertEqual(
        "Proper command usage: **~getserver**\nAliases include: **~getsrv**, **~gs**\n\nThis command will return the details of the server settings for the bot.",
        description, "Command not returned when it should have been valid")

  def test_valid_command(self):
    (valid, description) = helpservice.BuildCommandHelp("trainerinfo", False)
    self.assertEqual(True, valid,
                     "Command not returned when it should have been valid")
    self.assertEqual(
        "Proper command usage: **~trainerinfo *@user***\nAliases include: **~tinfo**, **~ti**\n\nThis command will give specific information regarding a trainer in the current server. If a user is mentioned within the command, it will show that users information. Information will include:\nPokedex %\nBadge  %\nTotal Pokemon count count\nShiny count",
        description, "Command not returned when it should have been valid")

  
  def test_full_help(self):
    fullHelp = helpservice.BuildFullHelp()
    self.assertEqual(3, len(fullHelp),
                     "Full help not returned when it should have")
    self.assertTrue(fullHelp[0].startswith("__**GENERAL INFO**__"),
                    "Commands returned are not valid.")
    self.assertTrue(fullHelp[1].startswith("__**GAMEPLAY**__"),
                    "Commands returned are not valid.")
    self.assertTrue(fullHelp[2].startswith("__**COMMANDS**__"),
                    "Commands returned are not valid.")
