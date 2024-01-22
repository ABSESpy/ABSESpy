In principle you aim to get a grid where each path or cell will represent a tree. (Should I work with patches or cells in the ABSES paradigm, will see). At each step, each tree will affect another tree nearby with a probability. If a tree is affected, that is, set on fire, it will burn down and won't be able to affect others.

It would be a good idea to just grab at certain checkpoints the state of the grid such that I can plot it and such that I can include this visual elements that ABSESpy is not really fully capable of displaying right now.


If I were to use a Model grid only and avoid .. well using Actors, what would that be like?

I would import the model class, then I would initialize a nature module as a layout. It is this layout I'd like to work with. There are patchcell at each position. Patch cells are of the class Patch Module and the question is where I can either create a new class of Patch cells that inherits also from the PatchCell module.


globals [
  initial-trees   ;; how many trees (green patches) we started with
  burned-trees    ;; how many have burned so far
]


breed [fires fire]    ;; bright red turtles -- the leading edge of the fire
breed [embers ember]  ;; turtles gradually fading from red to near black

to setup
  clear-all
  set-default-shape turtles "square"
  ;; make some green trees
  ask patches with [(random-float 100) < density]
    [ set pcolor green ]
  ;; make a column of burning trees
  ask patches with [pxcor = min-pxcor]
    [ ignite ]
  ;; set tree counts
  set initial-trees count patches with [pcolor = green]
  set burned-trees 0
  reset-ticks
end

to go
  if not any? turtles  ;; either fires or embers
    [ stop ]
  ask fires
    [ ask neighbors4 with [pcolor = green]
        [ ignite ]
      set breed embers ]
  fade-embers
  tick
end

;; creates the fire turtles
to ignite  ;; patch procedure
  sprout-fires 1
    [ set color red ]
  set pcolor black
  set burned-trees burned-trees + 1
end

;; achieve fading color effect for the fire as it burns
to fade-embers
  ask embers
    [ set color color - 0.3  ;; make red darker
      if color < red - 3.5     ;; are we almost at black?
        [ set pcolor color
          die ] ]
end


Oh it would look nice a graph visualization of some trade data. If and only if the spirit moves me, I shall proceed and do it. In a way, I must do it because I must genuinely want to it. I must burn of curiosity. Money is important but choose to live an austere life. Do not turn luxuries into necessities. I can have cold showers, exclusively. I can always walk, exclusively. I need not move a lot. I need not luxuries. I need to eat a ton. I need to smile to the people in my surroundings, whatever they are.

All in all, I want to live a rather boring, simple life where I mostly read and sleep. Work is a necessary evil. I also want to see people smile. I love seeing people smile. But that shouldn't put a cost to my soul. If need be, I will need to learn to endure solitude and deelpy appreciate every smile. I don't need sex but ejaculate oftentimes.