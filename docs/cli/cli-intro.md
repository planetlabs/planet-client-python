---
title: Command-line Interface (CLI) Introduction
---

## What is a CLI?

A command-line interface (CLI) was the original way everyone interacted with computers, before
the rise of '[Graphical User Interfaces](https://en.wikipedia.org/wiki/Graphical_user_interface)' (GUI).
With a CLI everything is done with text - you type commands in with your keyboard and the
responses are all textual. For more on what a command-line is see 
[this article](https://www.techtarget.com/searchwindowsserver/definition/command-line-interface-CLI).

## Why would I use Planet’s CLI?

Planet offers a number of ways to interact with its API’s, from 
[Planet Explorer](https://developers.planet.com/docs/apps/explorer/), which is a full 
web-based GUI, to [plug-ins for QGIS](https://developers.planet.com/docs/integrations/qgis/) 
and [ArcGIS Pro](https://developers.planet.com/docs/integrations/arcgis/) for those who want
to stay in their desktop GIS environment. 

The Planet CLI offers more direct interaction with the API’s, as its commands more directly
reflect what the API’s can do. Thus it can be a great way for developers to explore what is
possible. There are also many people who do lots of their day to day work on a command-line
and find it to be faster overall, so the Planet CLI will fit right in with their workflow. 

If you’re normally a GUI user but are curious about the command-line it does offer some
advantages. Once you’re comfortable with it, the CLI can be much faster for searching and
ordering lots of data. Many workflows that take lots of clicking in a UI can be just a
few keyboard commands. And you can further 'script' together many commands, so several
operations can be customized as one or two commands. So using a CLI can be a nice halfway
point between a full programming language and a GUI, offering a lot of power but without
having to become a programmer.

With Planet most new capabilities start in the API, and then the CLI often gets updated
before things are available in the UI’s. 

## How do I get started?

There are a couple main ways to get started, depending on how you like to learn. One way
is to just jump from here into all the examples in the [CLI for Data API Tutorial](cli-data.md)
and then the [CLI for Orders API Tutorial](cli-orders.md). You’ll quickly be able to get 
some results and start to get a feel for how things work, even if the exact commands make
less sense. Or you can continue in this document, and learn a bit more of the background
to understand what’s going on in the text you’re typing in. Or feel free to jump around
between the two.

### Complete Beginners

If you have never used a command-line interface before, we recommend learning some of the
basics before diving in here. One great place to start is the 
[Learn Enough Command Line to Be Dangerous](https://www.learnenough.com/command-line-tutorial),
but there are other options as well. Just be sure you are comfortable navigating through
different directories and modifying files, and the rest of this guide should teach you 
enough to understand Planet’s CLI.

## Core Unix Concepts

There are a few key CLI concepts that are worth understanding in order to get the most
out of Planet’s CLI. These are all built into any unix command-line, including Linux and 
the Mac terminal. If you’re on Windows you can use 
[Windows Subsytem for Linux](https://docs.microsoft.com/en-us/windows/wsl/about)
or [Cygwin](https://www.cygwin.com/).

### Piping & Redirection

Several commands in the Planet CLI are used to create files that are used as input to 
other commands. The default of these commands is to just print the output on your screen.
Seeing it on the screen can be useful for making sure it’s right, but you’ll most likely
want to make use of it. This is where the concept of ’redirection' comes in. If you use the 
`>` character and then specify a file name the command-line will save its output to that file.
So if you say:

```
 planet data filter --range cloud_percent lt 10 > filter.json
```

Then the output will be saved. This output is referred to as STDOUT, or 'standard output'. 
There is much more in this vein that you can do, like use `>>` to append to an existing
file, or `<` to send what’s in the file as input for a command. 

One of the most powerful concepts that we use extensively in the Planet CLI is 'piping'. 
The `|` is the pipe symbol, and it’s a special command that lets you pass the output from
one command to be the input for the next one. So instead of having to save to a file and
then referring to it you can just do it all in one call:

```
planet data filter --range cloud_percent lt 10 | planet data search PSScene --filter -
```

The pipe says to take the output of the first command and pass it to the input of 
the second. You’ll notice that the planet command has a dash (`-`), this is a convention
that is often used by different CLI programs to explicitly say ’read from
standard out'. Using the dash to mean
’read from standard out' is a general convention used by many programs, but it’s 
not universal, so check the docs of the program you’re using as to how it reads 
from piped input. For example GDAL/OGR uses a specific `/vsistdin/` convention to 
read from a pipe.

If you'd like to learn more about these topics then check out 
[this tutorial](https://ryanstutorials.net/linuxtutorial/piping.php). And if you'd
like to learn more about the dash (`-`) see 
[this tutorial](https://www.baeldung.com/linux/dash-in-command-line-parameters).

### Logical AND operator

Another command that is used in common Planet CLI is the `&&` command, which 
you put between two commands to say that the second command should only execute
when the first one is complete. It is used in `orders` to 
[wait and download](cli-orders.md#wait-then-download-an-order), so that the CLI
doesn't call the download command until the order is actually ready. 

### Variables

One of the more powerful constructs you can do in command-line environments is
to set and retrieve 'variables'. This starts you to get into true programming,
where you are saving values that you can retrieve at any time. This is often
useful with Planet’s CLI, especially in workflows that move between multiple 
different commands. You can find an introduction to variables and some powerful
constructs in this [tutorial](https://www.shellscript.sh/variables1.html).


### Running a command within another

While piping can take you quite far, there are some situations where it doesn't
quite handle exactly what you want. In many command-lines you can use the 
\` characters to wrap a set of commands that run. This is commonly done to set
variables like

```console
orderid=`planet orders list --limit 1 | jq -r .id`
```

## JQ

All of Planet’s API’s use [JSON](https://www.json.org/json-en.html) as their
main interchange format. So one of the most useful command-line tools is 
[`jq`](https://stedolan.github.io/jq/), which is a 'lightweight and 
flexible command-line JSON processor.' This allows you to easily manipulate
the output, searching through results and transforming them. You can see it 
used in the example above to extract just the order ID from the full orders API
JSON response. It also makes the default CLI output of any JSON much prettier, 
so throwing `| jq` at the end of any command returning JSON will be much more
readable. 

Check out https://ente.io/blog/tech/jq-diff/ for a decent tutorial - suggestions
for any betters ones appreciated!

## cURL

Another incredibly powerful and useful tool is [cURL](https://curl.se/). It’s 
the key tool to make any HTTP request from the command-line. There’s a good
[hands-on introduction](https://www.freecodecamp.org/news/how-to-start-using-curl-and-why-a-hands-on-introduction-ea1c913caaaa/)
from freeCodeCamp. 

## sed

One final tool worth mentioning is [`sed`](https://www.gnu.org/software/sed/manual/sed.html)
which lets you edit any text stream. While `jq` is focused on JSON, `sed`
can handle any string, and its used a few times to help further process
piped output.

## Collecting Results with `planet collect`

The final tool worth mentioning is part of the `planet` CLI, but is fairly
generic functionality that can be used with any command-line JSON output.

Some API calls, such as searching for imagery and listing orders, return a
varying, and potentially large, number of results. These API responses are
paged. The SDK manages paging internally and the associated CLI commands
output the results as a sequence. These results can be converted to a JSON blob
using the `collect` command. When the results
represent GeoJSON features, the JSON blob is a GeoJSON FeatureCollection.
Otherwise, the JSON blob is a list of the individual results.

```console
planet data search PSScene | planet collect -
```

This gives you a fully compliant GeoJSON FeatureCollection, which is 
understood by many more programs than the default 
[newline-delimited GeoJSON](https://stevage.github.io/ndgeojson/). 


