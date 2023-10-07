import unittest

from dataaccess.utility import replitdb
from globals import to_dict
from models.Pokemon import Pokemon
from services import pokemonservice


class PokemonTests(unittest.TestCase):

  def test_get_pokemon(self):
    result = pokemonservice.GetPokemon(171)
    self.assertIsNotNone(result, "Pokemon came back as None")
    self.assertEqual(171, result.Id if result else 0,
                     f"Id: {result.Id if result else 0} != 171")
    self.assertEqual(
        75, result.CaptureRate if result else 0,
        f"Capture rate: {result.CaptureRate if result else 0} != 75")
    self.assertEqual(
        4, result.FemaleChance if result else 0,
        f"Female Chance: {result.FemaleChance if result else 0} != 4")
    self.assertEqual("Lanturn", result.Name if result else 0,
                     f"Name: {result.Name if result else 0} != Lanturn")
    self.assertEqual(
        171, result.PokedexId if result else 0,
        f"Pokedex Id: {result.PokedexId if result else 0} != 171")
    self.assertEqual(12, result.Height if result else 0,
                     f"Height: {result.Height if result else 0} != 12")
    self.assertEqual(
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/171.png",
        result.Sprite if result else '',
        f"Basic Url: {result.Sprite if result else ''} != https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/171.png"
    )
    self.assertEqual(
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/shiny/171.png",
        result.ShinySprite if result else '',
        f"Shiny: {result.ShinySprite if result else ''} != https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/shiny/171.png"
    )
    self.assertIsNot(
        result.SpriteFemale if result else '',
        f"Female: {result.SpriteFemale if result else ''} != None")
    self.assertIsNot(
        result.ShinySpriteFemale if result else '',
        f"ShinyFemale: {result.ShinySpriteFemale if result else ''} != None")
    self.assertEqual(225, result.Weight if result else 0,
                     f"Weight: {result.Weight if result else 0} != 225")

    result = pokemonservice.GetPokemon(384)
    self.assertIsNotNone(result, "Pokemon came back as None")
    self.assertEqual(384, result.Id if result else 0,
                     f"Id: {result.Id if result else 0} != 384")
    self.assertEqual(
        45, result.CaptureRate if result else 0,
        f"Capture rate: {result.CaptureRate if result else 0} != 45")
    self.assertEqual(
        -1, result.FemaleChance if result else 0,
        f"Female Chance: {result.FemaleChance if result else 0} != -1")
    self.assertEqual("Rayquaza", result.Name if result else 0,
                     f"Name: {result.Name if result else 0} != Rayquaza")
    self.assertEqual(
        384, result.PokedexId if result else 0,
        f"Pokedex Id: {result.PokedexId if result else 0} != 384")
    self.assertEqual(70, result.Height if result else 0,
                     f"Height: {result.Height if result else 0} != 70")
    self.assertEqual(
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/384.png",
        result.Sprite if result else 0,
        f"Basic Url: {result.Sprite if result else 0} != https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/384.png"
    )
    self.assertEqual(
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/shiny/384.png",
        result.ShinySprite if result else 0,
        f"Shiny: {result.ShinySprite if result else 0} != https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/shiny/384.png"
    )
    self.assertIsNot(
        result.SpriteFemale if result else '',
        f"Female: {result.SpriteFemale if result else ''} != None")
    self.assertIsNot(
        result.ShinySpriteFemale if result else '',
        f"ShinyFemale: {result.ShinySpriteFemale if result else ''} != None")
    self.assertEqual(2065, result.Weight if result else 0,
                     f"Weight: {result.Weight if result else 0} != 2065")
