# Joker CGI Guestbook

This is a toy old-school
[CGI](https://en.wikipedia.org/wiki/Common_Gateway_Interface) guestbook
implemented in [Joker](https://joker-lang.org/), a dialect of Clojure.
The shebang line reflects that I wrote it
for use on the [SDF Public Access UNIX System](https://sdf.org).

## Description

The guestbook is a self-contained CGI script with no dependencies
except Joker 1.4.0 or later.
Like old CGI scripts, it has editable configuration at the top.
Data is stored in a [Bolt](https://github.com/etcd-io/bbolt) database,
which Joker has built in.
Captchas are stateless and use [HMAC](https://en.wikipedia.org/wiki/HMAC)
to verify the solved challenge is authentic and recent.
The secret key for HMAC is generated automatically and stored in the database.
This is a reason to forbid public access to it.

There is no management interface.
Use [boltbrowser](https://github.com/br0xen/boltbrowser)
to browse and edit the database.
To hide an entry without deleting it:

1. Find the entry in the Bolt bucket `entries`.
2. Edit the JSON object to add a key `hide` with the value `true`.

This project is a toy.
I don't know how actively I am going to maintain it.
Expect less testing, feature development, and support
than from a regular project.

## Screenshot

<a href="screenshot.png"><img alt="A screenshot of a webpage with three guestbook entries and a submit form" src="screenshot.png" width="320"></a>

## License

MIT.
See the file [`LICENSE`](LICENSE).
