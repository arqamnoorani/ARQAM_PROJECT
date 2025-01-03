import random  # For generating random numbers
import sys  # We will use sys.exit to exit the program
import pygame
import sqlite3  # For SQLite database
from pygame.locals import *  # Basic pygame imports

# Global variables for the game
FPS = 32
SCREENWIDTH = 289
SCREENHEIGHT = 511
SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
GROUNDY = SCREENHEIGHT * 0.8
GAME_SPRITES = {}
GAME_SOUNDS = {}
PLAYER_FRAMES = [
    r"D:\FlappyBird\gallery\sprites\redbird-upflap.png",
    r"D:\FlappyBird\gallery\sprites\redbird-midflap.png",
    r"D:\FlappyBird\gallery\sprites\redbird-downflap.png"
]
BACKGROUND = r"D:\FlappyBird\gallery\sprites\background-day.png"
PIPE = r"D:\FlappyBird\gallery\sprites\pipe-green.png"

# Initialize SQLite database
def create_db():
    conn = sqlite3.connect('flappybird.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            score INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_high_score():
    conn = sqlite3.connect('flappybird.db')
    c = conn.cursor()
    c.execute('SELECT MAX(score) FROM scores')
    high_score = c.fetchone()[0]
    conn.close()
    return high_score if high_score is not None else 0

def save_score(score):
    conn = sqlite3.connect('flappybird.db')
    c = conn.cursor()
    c.execute('INSERT INTO scores (score) VALUES (?)', (score,))
    conn.commit()
    conn.close()

def get_top_three_scores():
    conn = sqlite3.connect('flappybird.db')
    c = conn.cursor()
    c.execute('SELECT score FROM scores ORDER BY score DESC LIMIT 3')
    top_scores = c.fetchall()
    conn.close()
    return [score[0] for score in top_scores]  # Return a list of top three scores


def welcomeScreen():
    """
    Shows welcome images on the screen and top three scores
    """
    playerx = int(SCREENWIDTH / 5)
    playery = int((SCREENHEIGHT - GAME_SPRITES['player'][1].get_height()) / 2)
    messagex = int((SCREENWIDTH - GAME_SPRITES['message'].get_width()) / 2)
    messagey = int(SCREENHEIGHT * 0.13)
    basex = 0

    top_scores = get_top_three_scores()  # Fetch top 3 scores

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                return
            else:
                SCREEN.blit(GAME_SPRITES['background'], (0, 0))
                SCREEN.blit(GAME_SPRITES['player'][1], (playerx, playery))
                SCREEN.blit(GAME_SPRITES['message'], (messagex, messagey))
                SCREEN.blit(GAME_SPRITES['base'], (basex, GROUNDY))

                # Display top 3 scores in the place of the high score
                font = pygame.font.SysFont("comicsansms", 24)  # Reduced font size
                top_score_text = font.render("Top Scores", True, (255, 255, 255))
                outline_top_score_text = font.render("Top Scores", True, (0, 0, 0))

                # Adjusted position for "Top Scores" label
                SCREEN.blit(outline_top_score_text, (SCREENWIDTH / 2 - outline_top_score_text.get_width() / 2 + 2, SCREENHEIGHT / 2 + 90 + 2))
                SCREEN.blit(top_score_text, (SCREENWIDTH / 2 - top_score_text.get_width() / 2, SCREENHEIGHT / 2 + 90))

                # Render the top 3 scores, slightly higher and more compact
                for i, score in enumerate(top_scores):
                    score_text = font.render(f"{i + 1}. {score}", True, (255, 255, 255))
                    outline_score_text = font.render(f"{i + 1}. {score}", True, (0, 0, 0))

                    # Adjusted vertical positioning and compact layout
                    SCREEN.blit(outline_score_text, (SCREENWIDTH / 2 - outline_score_text.get_width() / 2 + 2, SCREENHEIGHT / 2 + 120 + i * 30 + 2))
                    SCREEN.blit(score_text, (SCREENWIDTH / 2 - score_text.get_width() / 2, SCREENHEIGHT / 2 + 120 + i * 30))

                pygame.display.update()
                FPSCLOCK.tick(FPS)




def mainGame():
    """
    The main game function
    """
    score = 0
    playerx = int(SCREENWIDTH / 5)
    playery = int(SCREENWIDTH / 2)
    basex = 0

    # Create 2 pipes for blitting on the screen
    newPipe1 = getRandomPipe()
    newPipe2 = getRandomPipe()

    upperPipes = [
        {'x': SCREENWIDTH + 200, 'y': newPipe1[0]['y']},
        {'x': SCREENWIDTH + 200 + (SCREENWIDTH / 2), 'y': newPipe2[0]['y']},
    ]
    lowerPipes = [
        {'x': SCREENWIDTH + 200, 'y': newPipe1[1]['y']},
        {'x': SCREENWIDTH + 200 + (SCREENWIDTH / 2), 'y': newPipe2[1]['y']},
    ]

    pipeVelX = -4

    playerVelY = -9
    playerMaxVelY = 10
    playerMinVelY = -8
    playerAccY = 1

    playerFlapAccv = -8  # Velocity while flapping
    playerFlapped = False  # It is true only when the bird is flapping

    animation_frame = 0  # Frame index for animation
    animation_counter = 0  # Frame timer to control animation speed

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                if playery > 0:
                    playerVelY = playerFlapAccv
                    playerFlapped = True
                    GAME_SOUNDS['wing'].play()

        crashTest = isCollide(playerx, playery, upperPipes, lowerPipes)
        if crashTest:
            save_score(score)  # Save score to the database
            display_game_over(score)  # Show game over screen
            return

        # Update score
        playerMidPos = playerx + GAME_SPRITES['player'][animation_frame].get_width() / 2
        for pipe in upperPipes:
            pipeMidPos = pipe['x'] + GAME_SPRITES['pipe'][0].get_width() / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                score += 1
                print(f"Your score is {score}")
                GAME_SOUNDS['point'].play()

        # Gravity effect
        if playerVelY < playerMaxVelY and not playerFlapped:
            playerVelY += playerAccY
        if playerFlapped:
            playerFlapped = False

        playerHeight = GAME_SPRITES['player'][animation_frame].get_height()
        playery = playery + min(playerVelY, GROUNDY - playery - playerHeight)

        # Move pipes to the left
        for upperPipe, lowerPipe in zip(upperPipes, lowerPipes):
            upperPipe['x'] += pipeVelX
            lowerPipe['x'] += pipeVelX

        # Add new pipe
        if 0 < upperPipes[0]['x'] < 5:
            newPipe = getRandomPipe()
            upperPipes.append(newPipe[0])
            lowerPipes.append(newPipe[1])

        # Remove pipes out of screen
        if upperPipes[0]['x'] < -GAME_SPRITES['pipe'][0].get_width():
            upperPipes.pop(0)
            lowerPipes.pop(0)

        # Update bird animation
        animation_counter += 1
        if animation_counter % 5 == 0:  # Change frame every 5 ticks
            animation_frame = (animation_frame + 1) % len(GAME_SPRITES['player'])

        # Update screen
        SCREEN.blit(GAME_SPRITES['background'], (0, 0))
        for upperPipe, lowerPipe in zip(upperPipes, lowerPipes):
            SCREEN.blit(GAME_SPRITES['pipe'][0], (upperPipe['x'], upperPipe['y']))
            SCREEN.blit(GAME_SPRITES['pipe'][1], (lowerPipe['x'], lowerPipe['y']))

        SCREEN.blit(GAME_SPRITES['base'], (basex, GROUNDY))
        SCREEN.blit(GAME_SPRITES['player'][animation_frame], (playerx, playery))

        # Draw score
        myDigits = [int(x) for x in list(str(score))]
        width = sum(GAME_SPRITES['numbers'][digit].get_width() for digit in myDigits)
        Xoffset = (SCREENWIDTH - width) / 2

        for digit in myDigits:
            SCREEN.blit(GAME_SPRITES['numbers'][digit], (Xoffset, SCREENHEIGHT * 0.12))
            Xoffset += GAME_SPRITES['numbers'][digit].get_width()

        pygame.display.update()
        FPSCLOCK.tick(FPS)

def isCollide(playerx, playery, upperPipes, lowerPipes):
    """
    Check if the player collides with a pipe or the ground
    """
    if playery > GROUNDY - 25 or playery < 0:
        GAME_SOUNDS['hit'].play()
        return True

    for pipe in upperPipes:
        pipeHeight = GAME_SPRITES['pipe'][0].get_height()
        if (
            playery < pipeHeight + pipe['y']
            and abs(playerx - pipe['x']) < GAME_SPRITES['pipe'][0].get_width()
        ):
            GAME_SOUNDS['hit'].play()
            return True

    for pipe in lowerPipes:
        if (
            playery + GAME_SPRITES['player'][0].get_height() > pipe['y']
            and abs(playerx - pipe['x']) < GAME_SPRITES['pipe'][0].get_width()
        ):
            GAME_SOUNDS['hit'].play()
            return True

    return False

def getRandomPipe():
    """
    Generate positions of two pipes (one bottom straight and one top rotated)
    """
    pipeHeight = GAME_SPRITES['pipe'][0].get_height()
    offset = SCREENHEIGHT / 3
    y2 = offset + random.randrange(
        0, int(SCREENHEIGHT - GAME_SPRITES['base'].get_height() - 1.2 * offset)
    )
    pipeX = SCREENWIDTH + 10
    y1 = pipeHeight - y2 + offset
    return [{'x': pipeX, 'y': -y1}, {'x': pipeX, 'y': y2}]

def display_game_over(score):
    """
    Display the Game Over screen
    """
    gameOverImage = GAME_SPRITES['gameover']
    gameOverX = (SCREENWIDTH - gameOverImage.get_width()) / 2
    gameOverY = SCREENHEIGHT / 3

    SCREEN.blit(gameOverImage, (gameOverX, gameOverY))
    font = pygame.font.SysFont("comicsansms", 30)

    # White text with black outline
    score_text = font.render(f"Your score: {score}", True, (255, 255, 255))
    outline_text = font.render(f"Your score: {score}", True, (0, 0, 0))

    # Blit the outline first
    SCREEN.blit(outline_text, (SCREENWIDTH / 2 - outline_text.get_width() / 2 + 2, SCREENHEIGHT / 2 + 50 + 2))  # Slightly offset
    SCREEN.blit(score_text, (SCREENWIDTH / 2 - score_text.get_width() / 2, SCREENHEIGHT / 2 + 50))
  

    pygame.display.update()
    pygame.time.wait(2000)  # Show Game Over screen for 2 seconds

if __name__ == "__main__":
    pygame.init()  # Initialize all pygame's modules
    FPSCLOCK = pygame.time.Clock()
    pygame.display.set_caption("Flappy Bird")

    # Initialize database
    create_db()
    

    # Load all game sprites
    GAME_SPRITES['numbers'] = tuple(
        pygame.image.load(rf"D:\FlappyBird\gallery\sprites\{i}.png").convert_alpha()
        for i in range(10)
    )
    GAME_SPRITES['message'] = pygame.image.load(
        r"D:\FlappyBird\gallery\sprites\message.png"
    ).convert_alpha()
    GAME_SPRITES['base'] = pygame.image.load(
        r"D:\FlappyBird\gallery\sprites\base.png"
    ).convert_alpha()
    GAME_SPRITES['pipe'] = (
        pygame.transform.rotate(pygame.image.load(PIPE).convert_alpha(), 180),
        pygame.image.load(PIPE).convert_alpha(),
    )

    # Load all bird frames
    GAME_SPRITES['player'] = tuple(
        pygame.image.load(frame).convert_alpha() for frame in PLAYER_FRAMES
    )

    GAME_SPRITES['background'] = pygame.image.load(BACKGROUND).convert()

    # Load game sounds
    GAME_SOUNDS['die'] = pygame.mixer.Sound(r"D:\FlappyBird\gallery\audio\die.wav")
    GAME_SOUNDS['hit'] = pygame.mixer.Sound(r"D:\FlappyBird\gallery\audio\hit.wav")
    GAME_SOUNDS['point'] = pygame.mixer.Sound(r"D:\FlappyBird\gallery\audio\point.wav")
    GAME_SOUNDS['swoosh'] = pygame.mixer.Sound(r"D:\FlappyBird\gallery\audio\swoosh.wav")
    GAME_SOUNDS['wing'] = pygame.mixer.Sound(r"D:\FlappyBird\gallery\audio\wing.wav")

    # Load game over image
    GAME_SPRITES['gameover'] = pygame.image.load(
        r"D:\FlappyBird\gallery\sprites\gameover.png"
    ).convert_alpha()

    while True:
        welcomeScreen()  # Show welcome screen
        mainGame()  # Run the main game loop
