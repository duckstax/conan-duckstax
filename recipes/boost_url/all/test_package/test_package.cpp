#include <boost/url/url_view.hpp>
#include <boost/url/static_pool.hpp>

int main(int, char**) {
    boost::urls::url_view  v("http://user:pass@example.com:80/path/to/file.txt?k1=v1&k2=v2");
    v.encoded_url() == "http://user:pass@example.com:80/path/to/file.txt?k1=v1&k2=v2";
    v.encoded_origin() == "http://user:pass@example.com:80";
    v.encoded_authority() == "user:pass@example.com:80";
    v.scheme() == "http";
    v.encoded_user() == "user";
    v.encoded_password() == "pass";
    v.encoded_userinfo() == "user:pass";
    v.encoded_host() == "example.com";
    v.port_part() == ":80";
    v.port() == "80";
    v.encoded_host_and_port() == "example.com:80";
    v.encoded_path() == "/path/to/file.txt";
    v.encoded_query() == "k1=v1&k2=v2";
    v.encoded_fragment() == "";

    v.user() == "user";
    v.password() == "pass";
    v.host() == "example.com";
    v.query() == "k1=v1&k2=v2";
    v.fragment() == "";
    return 0;
}
