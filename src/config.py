db_name = 'elif'
email_domain = 'insa-lyon.fr'
secret_key = '\xdf\x0e4\xaa\xdb:\xa8\xc6\r\x14\x96|\xc56\xfaq=\xb3\xb9\xc6\xaf\xab\x7fe'

logs_dir = 'logs'

length_limit = 90
min_password_length = 6

# Sample texting

default_description = """### This is your exercise's description.

Feel free to edit it. It should contain:

* A description of the problem the user should solve
* It's in [markdown](http://daringfireball.net/projects/markdown/syntax "Markdown's syntax")!
* It can contain [links](http://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=kp "Do not click this one!"), *different* _formatting, lists, ...
    - And sublists !
* Images:
![Alt text for your image](/static/img/cat.jpeg)
* And code:

        int magic_sort(vector<int> unsorted) {
            vector<int> sorted;
            foreach (int n : unsorted) {
                // Do stuff
            }
        }
"""

default_boilerplate_code = """#include <iostream>

int main() {
    int n;
    std::cin >> n;
    std::cout << n;
    return 0;
}
"""
