# GeniBot
a multi-tasking bot on Geni.com (using Geni API), a collaborative geneology site (or as I prefer, a wikipedia of the entire humanity).

For the moment, it is purely for my own use from the command line (not error-proof, and at places catered to my personal preferences for entering Chinese names). Anyone is welcome to use on their own, simply by requesting your own access token by logging into Geni, and click https://www.geni.com/platform/oauth/authorize?client_id=382&redirect_uri=a&response_type=token (it will appear in the address bar).

Feedback is most welcomed!

Per Geni policy, I must add that it is NOT in any way endorsed, operated, or sponsored by Geni.

## Things that have been done using this

* Fixing names that are in ALL CAPS or all small, with special treatment to names like McDonald.

* Moving Chinese names into the zh-TW or zh-CN tabs, so they will show up with surname first (and other "special effects" for Chinese names).

* Importing long lists from wikipedia or scholarly databases
** China Biographical Database (CBDB), ongoing
** Fellows of the Royal Society (full list in spreadsheet)
** A Finnish project at the request of a fellow curator: http://www.tverinkarjala.fi/muuttoluettelot.html

# Goal

In short: A bridge between [Geni.com](https://www.geni.com) and other "interest groups" (e.g., vintage photographs, history of an institution or an academic discripline) who are not already into conventional genealogy (i.e. interested in their own family history), so as to create a database or central hub for everything on and about every person ever walked the planet.

## What is Geni?

Geni's own mission, since it was launched in 2007, was to create a single family tree for the entire world, with a single profile for each and every person ever lived. What the public does not know is that Geni is, or has the potential to be, much more than just genealogy, but to be a platform which I would like to call a wikipedia for biographical data, with the core infrastructure on family relations (parent-child, including adoptions) while connections based on other human activities are accommodated by **timeline events** and **public projects**. It would resemble in one or another aspect the following three enterprises:

- wikipedia: only noteworthy people, and the structure is not specially designed for biographical data. They do have templates to that effect, but it poses quite a learning curve. Their advantage, of course, is that it blends into other non-biographical entries, their reputation as the first go-to place, and large number of active users who constantly correct mistakes and improve the contents.

- facebook: only living people (You can't make money off of dead people). Geni had actually started off trying to imitate the social media model, but could not scale by breaking out of the (relatively) small circle of genealogy enthusiasts.

- (scholarly) biographical databases: Most have poor user interface, and lack the technologies to "match" and "merge" the individual trees into a big network.


### Big Data: Geni's World Family Tree (The Big Tree)

In 2013, Geni provided their public "Big Tree" at the time to Yaniv Erlich, a geneticist researcher at MIT, who trimmed the data and stripped all the names, making it one of the largest dataset (43 million, and later upgraded to 86 million) for the new discipline of population genetics. Here's one of the things that they managed to do with this data: 

[![Human Migration](https://img.youtube.com/vi/fNY_oZaH3Yo/0.jpg)](https://www.youtube.com/watch?v=fNY_oZaH3Yo)

For a more technical overview, see [Yaniv's talk at Stanford](https://www.youtube.com/watch?v=einceXlGYCg)). Yaniv has gone on to Columbia, and started the New York Genome Center and [DNA.Land](https://dna.land). Most recently he became the Chief Science Officer at MyHeritage, which actually has been the parent company of Geni since 2012.

### Small Data

As the data on Geni is constantly improving (mostly importantly merging of duplicate profiles, resulting in an ever more intricately-connected network of the human species), it would be better to access the data as needed. It is impossilbe to download all the data, even just the bare network (of nodes and edges). So what can we do with small data?

Unbeknownst even to experierenced users, almost all the data on public profiles on Geni are actually accesible without an account, though the interface on Geni might be a little off-putting while logged out. Here's what you can get with a simple request on Charles Darwin: https://www.geni.com/api/profile-g6000000001779353747
(It's recommended to get a browser extension to display JSON type data in hierarchies, such as JSONView for Chrome.)


1. The most obvious application is to find if two people are related, by blood or marraige, in Geni's database. If they are suspected to be paternal cousins (e.g., having the same surname), one could run a simple script to check; Otherwise it'd be very computationally comsuming. To illustrate the challenge, one could simply take a look of how fast the "complete tree" grows around Charles Darwin: two steps out it measures at 173 profiles; at four steps, 812; at six steps, a whopping 3422. 

![Darwin](Darwin.jpg)

For a rare "home run" (while updating some data on Geni, with a cap of recursion depth at 150),

![stochastic](stochastic.jpg)

2. For a group of individuals (that are connected by profession, a particular event, etc.), see if they are related on Geni, sort of "minimal spanning tree". The cleanest, again, is paternal family: here's a tree connecting all the Darwins who are FRS (Fellows of the Royal Society)
