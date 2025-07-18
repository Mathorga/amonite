import pyglet
from pyglet.image import Texture
from pyglet.image.animation import Animation

# Sprite resource type alias.
SpriteRes: type[Animation | Texture] = pyglet.image.Texture | pyglet.image.animation.Animation

# Optional sprite resource type alias.
OptionalSpriteRes: type[Animation | Texture | None] = pyglet.image.Texture | pyglet.image.animation.Animation | None