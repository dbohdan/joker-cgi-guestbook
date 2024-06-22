#! /arpa/af/d/dbohdan/bin/joker
;; An old-school CGI guestbook written in Joker.
;; Version 0.1.0.
;;
;; Copyright (c) 2024 D. Bohdan
;;
;; Permission is hereby granted, free of charge, to any person obtaining a copy
;; of this software and associated documentation files (the "Software"), to deal
;; in the Software without restriction, including without limitation the rights
;; to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
;; copies of the Software, and to permit persons to whom the Software is
;; furnished to do so, subject to the following conditions:
;;
;; The above copyright notice and this permission notice shall be included in
;; all copies or substantial portions of the Software.
;;
;; THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
;; IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
;; FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
;; AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
;; LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
;; OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
;; THE SOFTWARE.

;; Change to `false` in production.
(def debug true)

(def db-file "guestbook.bolt")
;; The minimum wait time in seconds for posting from the same remote address.
(def min-wait (* 60 60))

(def css "
*, *::before, *::after {
  box-sizing: border-box;
}

input, textarea {
  font: inherit;
}

body {
  font-family: serif;
  font-size: 16px;
  margin: 0 1rem;
}

article {
  border: solid 0.15rem;
  border-radius: 12px;
  margin: 1rem 0;
  padding-left: 1rem;
}

form {
  display: flex;
  flex-direction: column;
}

form > div {
  padding: 0.25rem 0;
}

form input[type='text'], form textarea {
  margin-top: 0.15rem;
  width: 100%;
}
")

(def buckets
  {:entries "entries"
   :rate-limit "rate-limit"})

(def msgcat
  {:name "Name:"
   :contact "Contact:"
   :contact-in-form "Contact information (will be public):"
   :message "Message:"
   :rate-limited (str "Sorry, but your network address has "
                      "signed the guestbook recently.")
   :required-field-missing "Sorry, a name and a message are required."
   :title "Guestbook"
   :unknown-error "Sorry, an unknown error has occurred."})

(def statuses
  {:200 "200 OK"
   :422 "422 Unprocessable Entity"
   :429 "429 Too Many Requests"
   :500 "500 Internal Server Error"})

(defn parse-query
  "Parses the query part of a URI or a URL-encoded form."
  [query]
  (as-> query x
    (joker.string/trim x)
    (joker.string/split x "&")
    (mapcat
     (fn [pair]
       (rest
        (re-matches #"^([^=]*)=(.*)$" pair)))
     x)
    (map joker.url/query-unescape x)
    (apply hash-map x)))

(defn unix-now []
  (->
   (joker.time/now)
   (joker.time/unix)))

(defn rate-limited?
  "Checks if a remote address is being rate-limited
  as of the current timestap."
  [db remote current-timestamp]
  (let [last-timestamp
        (->
         (joker.bolt/get db (:rate-limit buckets) remote)
         (or "0")
         (joker.strconv/parse-int 10 0))]
    (> min-wait (- current-timestamp last-timestamp))))

(defn add-entry
  "Adds an entry to the guestbook and rate-limiting table."
  [db contact message name remote]
  (joker.bolt/put db
                  (:entries buckets)
                  (str (joker.bolt/next-sequence db (:entries buckets)))
                  (joker.json/write-string
                   {:contact contact
                    :message message
                    :name name
                    :remote remote}))
  (joker.bolt/put db
                  (:rate-limit buckets)
                  remote
                  (str (unix-now))))

(defn entry [{:strs [contact message name]}]
  [:dl
   [:dt (msgcat :name)] [:dd name]
   (when-not (joker.string/blank? contact)
     (list [:dt (msgcat :contact)] [:dd contact]))
   [:dt (msgcat :message)] [:dd message]])

(defn entries [bucket-contents]
  [:div
   (for [[_ json] bucket-contents]
     [:article (entry (joker.json/read-string json))])])

(defn entries-in-db [db]
  (->>
   (joker.bolt/by-prefix db (:entries buckets) "")
   (map (fn [[id json]]
          [(joker.strconv/parse-int id 10 0) json]))
   (sort)
   (entries)))

(defn form [action]
  [:form {:method :post
          :action action}
   [:div
    [:label {:for :name} (msgcat :name)]
    [:input {:type :text
             :id :name
             :name :name}]]
   [:div
    [:label {:for :contact} (msgcat :contact-in-form)]
    [:input {:type :text
             :id :contact
             :name :contact}]]
   [:div
    [:label {:for :message} (msgcat :message)]
    [:textarea {:id :message
                :name :message}]]
   [:div
    [:input {:type :submit}]]])

(defn html-view [status body & {:keys [title-prefix]}]
  (str
   "Content-Type: text/html\r\n"
   "Status: " status "\r\n\r\n"
   "<!doctype html>"
   (joker.hiccup/html
    {:mode :html}
    [:html {:lang "en"}
     [:head
      [:meta {:charset "utf-8"}]
      [:meta {:name "viewport" :content "width=device-width, initial-scale=1.0, user-scalable=yes"}]
      [:title
       (str
        (if (joker.string/blank? title-prefix)
          ""
          (str title-prefix " - "))
        (msgcat :title))]
      [:style (joker.hiccup/raw-string css)]]
     body])))

(defn error-view [status message]
  (html-view
   status
   [:body [:h1 message]]
   :title-prefix status))

(defn normal-view [db script-name]
  (html-view
   (:200 statuses)
   [:body
    (entries-in-db db)
    (form script-name)]))

(defn cgi
  "Process a CGI request with a given database, environment-variable
  dictionary, and standard input."
  [db env input]
  (try
    (let [query (parse-query input)
          contact (get query "contact" "")
          message (get query "message" "")
          name (get query "name" "")
          remote (get env "REMOTE_HOST" (get env "REMOTE_ADDR" ""))
          script-name (get env "SCRIPT_NAME" "")]
      (if (= (get env "REQUEST_METHOD" "") "POST")
        (if (rate-limited? db remote (unix-now))
          (error-view (:429 statuses) (msgcat :rate-limited))
          (if (or (joker.string/blank? name)
                  (joker.string/blank? message))
            (error-view (:422 statuses) (msgcat :required-field-missing))
            (do
              (add-entry db contact message name remote)
              (normal-view db script-name))))
        (normal-view db script-name)))
    (catch Error e
      (error-view (:500 statuses) (if debug e (msgcat :unknown-error))))))

(let [db (joker.bolt/open db-file 0600)]
  (dorun
   (for [bucket (vals buckets)]
     (joker.bolt/create-bucket-if-not-exists db bucket)))
  (print
   (cgi
    db
    (joker.os/env)
    (slurp *in*)))
  (joker.bolt/close db))
