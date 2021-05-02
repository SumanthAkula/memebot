# Version 1.420.69

**Core meme review system**
* Memes how have 2 ways of being reviewed: 
    * Reply
        * This is the same review system that was in place before, so nothing has changed here.
    * Reaction
        * Reaction ratings work by the meme reviewer reacting to whatever meme they want to review with `abdurkek`, `abdurcringe`, or `cursed`
        * The bot will then reply to the meme they just reacted to as a confirmation of the meme review being registered
    
* **Note: You cannot `preload` memes that were reviewed via reaction!** 
    * This means that if you react to a meme while the bot is offline, **that meme review will not be recorded when the `preload` command is run**
    * If the bot is offline, you can either just not review memes, or you can review them using the old "Reply" system.  
    
**Commands**
* `changelog` shows this message
* `leaderboard` now shows the total number of meme reviews each member has
* `help` now only shows commands that are available for your permission level to (i.e. bot admins will have a longer help message than regular members)
* `lastmeme` this is a new command that will tell the bot to reply to the last meme that was reviewed
* `split` removed this command
* `rating` now **requires** the `amount` parameter to be passed in.  previously you could leave it out, and the bot would assume `1` for that, but not anymore.

**Coming up**
* Some system to have the meme reviewer's memes be rated.  I was thinking of doing like a vote based reaction system for this but if y'all have any other ideas, lmk, and I'll see what I can do.  
* An improvement to the leaderboard's loading times.  I know it's slow as bricks I wrote the code for it at like 2AM one day and haven't touched it since.  