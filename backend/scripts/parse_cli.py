import argparse
from app.parsers.ollama_cv_parser import OllamaCVParser, display_parsing_results


def main():
    p = argparse.ArgumentParser(description="CLI to parse CV PDFs with OllamaCVParser")
    p.add_argument('file', help='PDF file to parse')
    p.add_argument('--sync', action='store_true', help='Run synchronously and print result')
    p.add_argument('--model', default='llama3.1:8b')
    args = p.parse_args()

    parser = OllamaCVParser(model=args.model)
    doc = parser.parse(args.file)

    if args.sync:
        print(display_parsing_results(doc))
    else:
        print('Parse scheduled (local).')


if __name__ == '__main__':
    main()
