# Joker CGI Guestbook

This is a toy old-school
[CGI](https://en.wikipedia.org/wiki/Common_Gateway_Interface) guestbook
implemented in [Joker](https://joker-lang.org/), a dialect of Clojure.
The shebang line reflects that I wrote it
for use on the [SDF Public Access UNIX System](https://sdf.org).

## Description

The guestbook is a self-contained CGI script with no dependencies.
Like old CGI scripts, it has editable configuration at the top.
Data is stored in a [Bolt](https://github.com/etcd-io/bbolt) database,
which Joker has built in.
Captchas are stateless and use [HMAC](https://en.wikipedia.org/wiki/HMAC)
to verify the solved challenge is authentic and recent.
The secret key for HMAC is generated automatically and stored in the database.
This is a reason to forbid public access to it.

Use [boltbrowser](https://github.com/br0xen/boltbrowser)
to browse and edit the database.

## Screenshot

<a href="screenshot.png"><img alt="A screenshot of a webpage with three guestbook entries and a submit form" src="screenshot.png" width="320" height="569"></a>

## License

MIT.
See the file [`LICENSE`](LICENSE).
