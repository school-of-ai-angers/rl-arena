# Start Django in stand-alone mode
import django
django.setup()

if __name__ == "__main__":
    from builder.builder import main

    main()
