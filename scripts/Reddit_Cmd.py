import asyncpraw
from bs4 import BeautifulSoup

class Reddit_Command:
    async def __new__(self, ctx, subreddit, limit, loop, getenv, random, requests, discord):
        if loop > 100:
            await ctx.send("The loop times must be less than a 100!")
            return
        if loop > limit:
            loop = limit

        self.reddit = asyncpraw.Reddit(client_id=getenv('CLIENT_ID'), client_secret=getenv('CLIENT_SECRET'), username=getenv('USERNAME'), password=getenv('PASSWORD'), user_agent="NO")
        self.subreddit = await self.reddit.subreddit(subreddit)
        self.top = self.subreddit.top(limit=limit)
        try:
            self.all_posts = [sub async for sub in self.top]
        except Exception:
            await ctx.send(f"Subreddit not found.")
        else:
            self.ctx = ctx
            self.random = random
            self.loop = loop
            self.requests = requests
            self.discord = discord

            await self.send(self)

    
    async def send(self):
        for i in range(self.loop):
            self.sub = self.random(self.all_posts)
            self.all_posts.remove(self.sub) # Just remove to make it so it won't report the same thing
            url, title = self.sub.url, self.sub.title
            if not url.endswith('.gifv'):
                video_url = await self.get_video(self, url)
            else:
                video_url = url

            if video_url.endswith('.mp4'):
                await self.ctx.send(f"**{title}**\n{i + 1}/{self.loop}: {video_url}")
            elif video_url[-4] == '.':
                embed = self.discord.Embed(title=title)
                embed.set_image(url=video_url)
                embed.set_footer(text=f'{i + 1}/{self.loop}')
                await self.ctx.send(embed=embed)
            else:
                await self.ctx.send(f"**{title}**\n{i + 1}/{self.loop}: {url}")



    async def get_video(self, url):
        page = self.requests.get(url)
        bSoup = BeautifulSoup(page.content, 'html.parser')
        link_list = bSoup.find_all('source')
        
        for link in link_list:
            try:
                if not link['src'] == '':
                    url = link['src']
                    return url
            except KeyError: pass

        return url