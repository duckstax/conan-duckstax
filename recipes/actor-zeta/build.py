from utils import is_pure_c,get_builder_default
import os

if __name__ == "__main__":
    recipe_is_pure_c = is_pure_c()
    builder = get_builder_default(pure_c=recipe_is_pure_c, cwd=os.path.dirname(os.path.abspath(__file__)))
    builder.run()
