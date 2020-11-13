# Two-Faced-Type

## What is this?
The original idea was to generate objects that look like different letters from different angles. These pairs of letters could then be combined into words, like [this](https://www.behance.net/gallery/26043529/Two-Faced-Type).

![Example Image](https://mir-s3-cdn-cf.behance.net/project_modules/max_1200/7c0cfc26043529.5634f0cc35e86.jpg)

These seem relatively time-consuming to draw or create by hand. I'd like to 3D-print them, so why not have software do it for me?

## Planning/Approach
TODO: Describe initial idea/algorithm and why it wouldn't work
* Had issue with V/T combo, V would not line up with base of T

### Core Idea
1. Take 2 letters, each represented as contiguous 2d surfaces
2. Put either letter on adjacent sides of an imaginary cube
3. Extrude the first letter through the cube
4. Take the invserse of the second letter, and project that through the cube, removing all the material
5. This will leave material that appears to be one letter from one angle, and another letter from a different angle
6. However, there may be redundant geometry. To remove this, raycast from both sides the cube would be viewed from. Any geometry the ray doesn't hit can be marked as redundant. After casting from both directions, geometry that is redundant from both sides can be removed.

### Main Components needed
[pythonocc](http://tenko.github.io/occmodel/examples.html) seems like a good candidate to handle most of this. 

##### How to represent surfaces in Python
http://tenko.github.io/occmodel/examples.html#faces

##### Read PNGs or SVGs to this surface geometry
READ library, create faces
http://tenko.github.io/occmodel/examples.html#faces

##### Projecting surfaces, and taking inverses
http://tenko.github.io/occmodel/examples.html#faces
http://tenko.github.io/occmodel/examples.html#solids

##### Breaking up geometry and casting
Something like https://github.com/tpaviot/pythonocc-core/issues/530

##### Converting final geometry to STL
https://pythonocc.wordpress.com/2013/02/26/creating-an-stl-file-from-a-pythonocc-shape/



