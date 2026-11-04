#include <iostream>

#include <integration/cpp/otterbrix.hpp>

int main() {
    auto otterbrix = otterbrix::make_otterbrix_or_exit(configuration::config::create_config("otterbrix_test_package_data"));
    std::cout << "Otterbrix test package running!" << std::endl;
    return 0;
}
