#include <goblin-engineer.hpp>
#include <goblin-engineer/components/network.hpp>

#include <boost/asio.hpp>
#include <boost/beast/core.hpp>
#include <boost/beast/http.hpp>
#include <boost/beast/version.hpp>
#include <chrono>
#include <ctime>
#include <iostream>
#include <memory>

namespace beast = boost::beast;   // from <boost/beast.hpp>
namespace http = beast::http;     // from <boost/beast/http.hpp>
namespace net = boost::asio;      // from <boost/asio.hpp>
using tcp = boost::asio::ip::tcp; // from <boost/asio/ip/tcp.hpp>

int main() {
  goblin_engineer::components::root_manager app(1, 1000);
  return 0;
}
