---
title: Command-line Interface (CLI) Concepts
---

Planet's command-line interface is built of composable pieces that combine in powerful ways.
To take full advantage of all that Planet's CLI offers there are a few concepts and tools
that are worth explaining. 

**NOTE:** This document is still a work in progress, but we'll work to flesh it out. We'll
leave it up since there's still a bit of good information.

## Core Unix Concepts

If you are completely new to the command-line we recommend starting with a real introductory
guide like (TODO, link to a good guide). But we wanted to go over a few key concepts that 
are a bit more 'advanced', as they allow you to get the most out of Planet's CLI. These are
all built into any unix command-line, including Linux and the Mac terminal. If you're on 
Windows you can use [Windows Subsytem for Linux](https://docs.microsoft.com/en-us/windows/wsl/about)
or [Cygwin](https://www.cygwin.com/).

### Piping & Redirection

Several commands in the Planet CLI are used to create files that are used as input to 
other commands. The default of these commands is to just print the output on your screen.
Seeing it on the screen can be useful for making sure it's right, but you'll most likely
want to make use of it. This is where the concept of 'redirection' comes in. If you use the 
`>` character and then specify a file name the command-line will save its output to that file.
So if you say:

```
 planet data filter --range cloud_percent lt 10 > filter.json
```

Then the output will be saved. This output is referred to as STDOUT, or 'standard output'. 
There is much more in this vein that you can do, like use `>>` to append to an existing
file, or `<` to send what's in the file as input for a command. 

One of the most powerful concepts that we use extensively in the Planet CLI is 'piping'. 
The `|` is the pipe symbol, and it's a special command that lets you pass the output from
one command to be the input for the next one. So instead of having to save to a file and
then referring to it you can just do it all in one call:

```
planet data filter --range cloud_percent lt 10 | planet data search-quick PSScene -
```

The pipe says to take the output of the first command and pass it to the input of 
the second. You'll notice that the planet command has a dash (`-`), this is a convention
that is often used by different CLI programs to explicitly say 'read from
standard out'. Most Planet CLI commands require it, but one or two will implicitly
read from standard out if it's not explicitly included. Using the dash to mean
'read from standard out' is a general convention used by many programs, but it's 
not universal, so check the docs of the program you're using as to how it reads 
from piped input. For example GDAL/OGR uses a specific `/vsistdin/` convention to 
read from a pipe.

If you'd like to learn more about these topics then check out 
[this tutorial](https://ryanstutorials.net/linuxtutorial/piping.php). And if you'd
like to learn more about the dash (`-`) see 
[this tutorial](https://www.baeldung.com/linux/dash-in-command-line-parameters).


### head & tail

Also less/more?

### Running a command within another

### variables

## JQ

## curl

## sed

