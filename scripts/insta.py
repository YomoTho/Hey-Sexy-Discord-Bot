from instabot import Bot


class Instagram_Bot:
	def __init__(self, sys, requests, shutil, os):
		self.sys = sys
		self.requests = requests
		self.shutil = shutil
		self.os = os

	async def upload(self, caption=""):
		print(f"caption = {caption}")
		bot = Bot()

		bot.login(username='awww_cuteness', password='Awesome4747')

		bot.upload_photo("image.jpg", caption=caption)

		print("Done?")


	async def downlaod_image(self, link):
		print("Downloading image...")
		response = self.requests.get(link)

		photo = open("image.jpg", 'wb')
		photo.write(response.content)
		photo.close()
		print("Done downloading image.")


	async def clean_up(self):
	    print("Cleaning up...")
	    dir = "config"
	    remove_me = "imgs\img.jpg.REMOVE_ME"
	    # checking whether config folder exists or not
	    if self.os.path.exists(dir):
	        try:
	            # removing it because in 2021 it makes problems with new uploads
	            self.shutil.rmtree(dir)
	        except OSError as e:
	            print("Error: %s - %s." % (e.filename, e.strerror))
	    if self.os.path.exists(remove_me):
	        src = self.os.path.realpath("imgs\img.jpg")
	        self.os.rename(remove_me, src)
	    print("Done cleaning up.")


	async def main(self, url, caption):
		await self.clean_up()
		await self.downlaod_image(url)
		await self.upload(caption)