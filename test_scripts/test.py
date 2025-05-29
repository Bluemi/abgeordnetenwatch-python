from models.politicians import get_politicians


def main():
    politicians = get_politicians(first_name='friedrich')
    for p in politicians:
        print(p)
    print(politicians)


if __name__ == '__main__':
    main()
