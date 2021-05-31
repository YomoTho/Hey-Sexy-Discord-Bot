import asyncpraw
import json
import discord
import asyncio
from random import choice
from os import getenv



class Reddit:
    def __init__(self) -> None:
        self.reddit = asyncpraw.Reddit(
            client_id=getenv('CLIENT_ID'), 
            client_secret=getenv('CLIENT_SECRET'), 
            username=getenv('USERNAME'), 
            password=getenv('PASSWORD'), 
            user_agent="NO"
        )
        self.reddit_json_path = '../data/nsfw_subreddit.json'
        self.nsfw_subreddit = self.read_json()


    def read_json(self):
        with open(self.reddit_json_path) as f:
            return json.load(f)


    def save_json(self, content:dict):
        with open(self.reddit_json_path, 'w') as f:
            json.dump(content, f, indent=4)



    async def __call__(self, ctx, sub_reddit:str, loop:int=1):
        try:
            self.nsfw_subreddit = self.read_json()

            loop = int(loop)
            if loop > 100:
                return await ctx.send("The loop must be less than 100!")
            if not ctx.channel.is_nsfw():
                if sub_reddit in self.nsfw_subreddit['nsfw']:
                    return await ctx.send("This is not a NSFW text channel.")

            limit = (loop * 10) if loop > 10 else 50
            self.subreddit = await self.reddit.subreddit(sub_reddit)

            self.all_post = []

            async for submission in self.subreddit.hot(limit=limit):
                self.all_post.append(submission)
            else:
                if self.all_post[0].over_18:
                    if not sub_reddit in self.nsfw_subreddit['nsfw']:
                        self.nsfw_subreddit['nsfw'].append(sub_reddit)
                        self.save_json(self.nsfw_subreddit)
                    if not ctx.channel.is_nsfw():
                        return await ctx.send("This is not a NSFW text channel.")
                
                for i in range(loop):
                    subm = choice(self.all_post)
                    self.all_post.remove(subm)
                    
                    url, title = subm.url, subm.title
                
                    video_url = url

                    if video_url.endswith('.mp4'):
                        await ctx.send(f"**{title}**\n{i + 1}/{loop}: {video_url}")
                    elif video_url[-4] == '.':
                        embed = discord.Embed(title=title)
                        embed.set_image(url=video_url)
                        embed.set_footer(text=f'{i + 1}/{loop}')
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(f"**{title}**\n{i + 1}/{loop}: {url}")
        except Exception as e:
            if str(e) == 'Redirect to /subreddits/search':
                await ctx.send("Sub Reddit not found.")
            else:
                await ctx.send(str(e))