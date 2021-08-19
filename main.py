import pygame
from pygame.locals import *
from pygame import mixer
import pickle
from os import path

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()
clock = pygame.time.Clock()
fps = 60

#ukuran layar dan nama game
screen_width = 600
screen_height = 600
screen = pygame.display.set_mode((screen_width,screen_height))
pygame.display.set_caption('Platformer Game')

#font untuk coin
font_score = pygame.font.SysFont('Bauhaus 93', 25)

#nilai awal variable
tile_size = 30
game_over = 0
main_menu = True
level = 1
max_levels = 5
score = 0

#warna font
white = (255, 255, 255)

#mengambil gambar dari folder img
sun_img = pygame.image.load('img/sun.png')
bg_img = pygame.image.load('img/sky.png')
restart_img = pygame.image.load('img/restart.png')
start_img = pygame.image.load('img/start.png')
exit_img = pygame.image.load('img/exit.png')
win_img = pygame.image.load('img/win.png')
lose_img = pygame.image.load('img/lose.png')

#memasukkan musik dari folder music dan mengatur musik
pygame.mixer.music.load('music/music.wav')
pygame.mixer.music.play(-1, 0.0, 5000)
coin_fx = pygame.mixer.Sound('music/coin.wav')
coin_fx.set_volume(0.5)
jump_fx = pygame.mixer.Sound('music/jump.wav')
jump_fx.set_volume(0.5)
game_over_fx = pygame.mixer.Sound('music/game_over.wav')
game_over_fx.set_volume(0.5)

def draw_text(text, font, text_col, x, y):
	img = font.render(text, True, text_col)
	screen.blit(img, (x, y))

#fungsi untuk mereset level
def reset_level(level):
	player.reset(60, screen_height - 78)
	blob_group.empty()
	platform_group.empty()
	coin_group.empty()
	lava_group.empty()
	exit_group.empty()

	#memasukkan data level dari 1-5
	if path.exists(f'level{level}_data'):
		pickle_in = open(f'level{level}_data', 'rb')
		world_data = pickle.load(pickle_in)
	world = World(world_data)

	#membuat koin untuk menampilkan skor
	score_coin = Coin(tile_size // 2, tile_size // 2)
	coin_group.add(score_coin)

	return world


class Button():
	def __init__(self, x, y, image):
		self.image = image
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.clicked = False

	def draw(self):
		action = False

		#get mouse position
		pos = pygame.mouse.get_pos()

		#check mouseover and clicked conditions
		if self.rect.collidepoint(pos):
			if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
				action = True
				self.clicked = True

		if pygame.mouse.get_pressed()[0] == 0:
			self.clicked = False


		#draw button
		screen.blit(self.image, self.rect)

		return action

#pengaturan pemain
class Player():
	def __init__(self, x, y):
		self.reset(x, y)

	def update(self,game_over):
		dx = 0
		dy = 0
		walk_cooldown = 5
		col_thresh = 20

		if game_over == 0:
			#yang digunakan untuk menggerakkan pemain dan perpindahannya
			key = pygame.key.get_pressed()
			if key[pygame.K_UP] and self.jumped == False and self.in_air == False:
				jump_fx.play()
				self.vel_y = -12
				self.jumped = True
			if key[pygame.K_UP] == False:
				self.jumped = False
			if key[pygame.K_LEFT]:
				dx -= 3
				self.counter += 1
				self.direction = -1
			if key[pygame.K_RIGHT]:
				dx += 3
				self.counter += 1
				self.direction = 1
			if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False:
				self.counter = 0
				self.index = 0
				if self.direction == 1:
					self.image = self.images_right[self.index]
				if self.direction == -1:
					self.image = self.images_left[self.index]

			# animasi
			if self.counter > walk_cooldown:
				self.counter = 0
				self.index += 1
				if self.index >= len(self.images_right):
					self.index = 0
				if self.direction == 1:
					self.image = self.images_right[self.index]
				if self.direction == -1:
					self.image = self.images_left[self.index]

			#membuat gravitasi
			self.vel_y += 1
			if self.vel_y > 10:
				self.vel_y = 10
			dy += self.vel_y

			#menambahkan collision
			self.in_air = True
			for tile in world.tile_list:
				# collision arah horizontal
				if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
					dx = 0
				# collision arah vertikal
				if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
					# collision saat melompat
					if self.vel_y < 0:
						dy = tile[1].bottom - self.rect.top
						self.vel_y = 0
					# collision saat jatuh
					elif self.vel_y >= 0:
						dy = tile[1].top - self.rect.bottom
						self.vel_y = 0
						self.in_air = False

			# collision dengan slime
			if pygame.sprite.spritecollide(self, blob_group, False):
				game_over = -1
				game_over_fx.play()

			# collision jika mengenai lava
			if pygame.sprite.spritecollide(self, lava_group, False):
				game_over = -1
				game_over_fx.play()

			# collision jika mengenai pintu(exit)
			if pygame.sprite.spritecollide(self, exit_group, False):
				game_over = 1

			# collision dengan platform
			for platform in platform_group:
				# collision arah horizontal
				if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
						dx = 0
				# collision arah vertikal
				if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
					# collision saat ada di bawah platform
					if abs((self.rect.top + dy) - platform.rect.bottom) < col_thresh:
						self.vel_y = 0
						dy = platform.rect.bottom - self.rect.top
					# collision saat ada di atas platform
					elif abs((self.rect.bottom + dy) - platform.rect.top) < col_thresh:
						self.rect.bottom = platform.rect.top - 1
						self.in_air = False
						dy = 0
					# bergerak dengan platform
					if platform.move_x != 0:
						self.rect.x += platform.move_direction

			#update posisi pemain
			self.rect.x += dx
			self.rect.y += dy

		elif game_over == -1:
			self.image = self.dead_image
			screen.blit(lose_img, ((screen_width // 2) - 110, screen_height // 2 - 130))
			if self.rect.y > 200:
				self.rect.y -= 5

		#menampilkan pemain ke layar
		screen.blit(self.image, self.rect)

		return game_over

	def reset(self, x, y):
		self.images_right = []
		self.images_left = []
		self.index = 0
		self.counter = 0
		for num in range(1, 11):
			img_right = pygame.image.load(f'img/Walk{num}.png')
			img_right = pygame.transform.scale(img_right, (24, 48))
			img_left = pygame.transform.flip(img_right, True, False)
			self.images_right.append(img_right)
			self.images_left.append(img_left)
		self.dead_image = pygame.image.load('img/ghost1.png')
		self.image = self.images_right[self.index]
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.width = self.image.get_width()
		self.height = self.image.get_height()
		self.vel_y = 0
		self.jumped = False
		self.direction = 0
		self.in_air = True

class World():
	def __init__(self, data):
		self.tile_list = []

		#load images
		dirt_img = pygame.image.load('img/dirt.png')
		grass_img = pygame.image.load('img/grass.png')


		row_count = 0
		for row in data:
			col_count = 0
			for tile in row:
				if tile == 1:
					img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
					img_rect = img.get_rect()
					img_rect.x = col_count * tile_size
					img_rect.y = row_count * tile_size
					tile = (img, img_rect)
					self.tile_list.append(tile)
				if tile == 2:
					img = pygame.transform.scale(grass_img, (tile_size, tile_size))
					img_rect = img.get_rect()
					img_rect.x = col_count * tile_size
					img_rect.y = row_count * tile_size
					tile = (img, img_rect)
					self.tile_list.append(tile)
				if tile == 3:
					blob = Enemy(col_count * tile_size, row_count * tile_size + 12)
					blob_group.add(blob)
				if tile == 4:
					platform = Platform(col_count * tile_size, row_count * tile_size, 1, 0)
					platform_group.add(platform)
				if tile == 5:
					platform = Platform(col_count * tile_size, row_count * tile_size, 0, 1)
					platform_group.add(platform)
				if tile == 6:
					lava = Lava(col_count * tile_size, row_count * tile_size + (tile_size // 2))
					lava_group.add(lava)
				if tile == 7:
					coin = Coin(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
					coin_group.add(coin)
				if tile == 8:
					exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
					exit_group.add(exit)
				col_count += 1
			row_count += 1

	def draw(self):
		for tile in self.tile_list:
			screen.blit(tile[0], tile[1])


class Enemy(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.image.load('img/blob1.png')
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.move_direction = 1
		self.move_counter = 0

	def update(self):
		self.rect.x += self.move_direction
		self.move_counter += 1
		if abs(self.move_counter) > 30:
			self.move_direction *= -1
			self.move_counter *= -1

class Platform(pygame.sprite.Sprite):
	def __init__(self, x, y, move_x, move_y):
		pygame.sprite.Sprite.__init__(self)
		img = pygame.image.load('img/platform.png')
		self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.move_counter = 0
		self.move_direction = 1
		self.move_x = move_x
		self.move_y = move_y

	def update(self):
		self.rect.x += self.move_direction * self.move_x
		self.rect.y += self.move_direction * self.move_y
		self.move_counter += 1
		if abs(self.move_counter) > 30:
			self.move_direction *= -1
			self.move_counter *= -1


class Lava(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		img = pygame.image.load('img/lava.png')
		self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y

class Coin(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		img = pygame.image.load('img/coin.png')
		self.image = pygame.transform.scale(img, (tile_size // 2, tile_size // 2))
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)

class Exit(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		img = pygame.image.load('img/exit1.png')
		self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 1.5)))
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y


player = Player(60, screen_height - 78)
blob_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

#membuat koin
score_coin = Coin(tile_size // 2, tile_size // 2)
coin_group.add(score_coin)

#memasukkan data level
if path.exists(f'level{level}_data'):
	pickle_in = open(f'level{level}_data', 'rb')
	world_data = pickle.load(pickle_in)
world = World(world_data)

#membuat buttons
restart_button = Button(screen_width // 2 - 30, screen_height // 2 - 20, restart_img)
start_button = Button(screen_width // 2 - 130, screen_height // 2 - 20, start_img)
exit_button = Button(screen_width // 2 + 30, screen_height // 2 - 20, exit_img)

run = True
while run :
	clock.tick(fps)
	screen.blit(bg_img,(0,0))
	screen.blit(sun_img,(50,50))
	if main_menu == True:
		if exit_button.draw():
			run = False
		if start_button.draw():
			main_menu = False
	else:
		world.draw()

		if game_over == 0:
			blob_group.update()
			platform_group.update()
			# update score
			# check if a coin has been collected
			if pygame.sprite.spritecollide(player, coin_group, True):
				score += 1
				coin_fx.play()
			draw_text('X ' + str(score), font_score, white, tile_size , 0)

		blob_group.draw(screen)
		platform_group.draw(screen)
		lava_group.draw(screen)
		coin_group.draw(screen)
		exit_group.draw(screen)
		game_over = player.update(game_over)


		#yang terjadi jika pemain mati
		if game_over == -1:
			if restart_button.draw():
				world_data = []
				world = reset_level(level)
				game_over = 0
				score = 0

		# yang terjadi jika pemain berhasil menyelesaikan level
		if game_over == 1:
			# mereset game dan menuju level selanjutnya
			level += 1
			if level <= max_levels:
				# mereset level
				world_data = []
				world = reset_level(level)
				game_over = 0
			else:
				screen.blit(win_img, ((screen_width // 2) - 110, screen_height // 2 - 130))
				if restart_button.draw():
					level = 1
					# mereset level
					world_data = []
					world = reset_level(level)
					game_over = 0
					score = 0


	for event in pygame.event.get():
		if event.type == pygame.QUIT :
			run = False

	pygame.display.update()

pygame.quit()