import os

from dotenv import load_dotenv

from learning_canvas import LearningCanvas
load_dotenv()

BOOK_PATH=os.getenv("BOOK_PATH")

def interact(learning_canvas: LearningCanvas):
    while True:
        mode = input("Choose mode: (s)earch, (a)nswer query, (h)istory, (q)uit: ").strip().lower()
        if mode == 's':
            search_term = input("Enter a search query: ")
            learning_canvas.search_query(search_term)
        elif mode == 'a':
            query = input("Enter your question: ")
            learning_canvas.answer_query(query)
        elif mode == 'h':
            learning_canvas.get_user_history("user_123")
        elif mode == 'q':
            break
        else:
            print("Invalid choice. Please choose s, a, h, or q.")


def build_knowledge(learning_canvas: LearningCanvas, book_path):
    for epub_file in process_epub_files(book_path):
        if os.path.exists(epub_file):
            learning_canvas.add_epub(epub_file, user_id="user_123")
        else:
            print(f"EPUB file '{epub_file}' not found.")

            
def process_epub_files(folder_path):
    """Iterates over a folder and processes only EPUB files."""
    if not os.path.exists(folder_path):
        print(f"Folder path {folder_path} does not exist.")
        return

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".epub"):
            yield os.path.join(folder_path, file_name)

if __name__ == "__main__":

    canvas = LearningCanvas()
    try:
        build_knowledge(canvas, BOOK_PATH)
        interact(canvas)
    except Exception as e:
        print(e)
    finally:
        canvas.close()



