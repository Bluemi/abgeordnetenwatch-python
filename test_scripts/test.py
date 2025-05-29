from models.parliament_period import get_parliament_periods
from models.politicians import get_politicians


def main_politicians():
    politicians = get_politicians(first_name='friedrich')
    for p in politicians:
        print(p)


def main_parliament_period():
    periods = get_parliament_periods(id=87)
    print(periods)


if __name__ == '__main__':
    # main_politicians()
    main_parliament_period()
