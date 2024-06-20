#! /arpa/af/d/dbohdan/bin/joker
;; An old-school CGI guestbook written in Joker.
;; Copyright (c) 2024 D. Bohdan.
;; License: MIT.

(def db-file "guestbook.bolt")
(def entries-bucket "entries")
(def rate-limit-bucket "rate-limit")
(def rate-limit (* 60 60))

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
         (joker.bolt/get db rate-limit-bucket remote)
         (or "0")
         (joker.strconv/parse-int 10 0))]
    (< (- current-timestamp last-timestamp) rate-limit)))

(defn add-entry
  "Adds an entry to the guestbook and rate-limiting table."
  [db contact message name remote]
  (joker.bolt/put db
                  entries-bucket
                  (str (joker.bolt/next-sequence db entries-bucket))
                  (joker.json/write-string
                   {:contact contact
                    :message message
                    :name name
                    :remote remote}))
  (joker.bolt/put db
                  rate-limit-bucket
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
   (joker.bolt/by-prefix db entries-bucket "")
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
    [:textarea {:name :message}]]
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
      [:title
       (str
        (if (joker.string/blank? title-prefix)
          ""
          (str title-prefix " - "))
        (msgcat :title))]]
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
    (catch Error _
      (error-view (:500 statuses) (msgcat :unknown-error)))))

(let [db (joker.bolt/open db-file 0600)]
  (joker.bolt/create-bucket-if-not-exists db entries-bucket)
  (joker.bolt/create-bucket-if-not-exists db rate-limit-bucket)
  (print
   (cgi
    db
    (joker.os/env)
    (slurp *in*)))
  (joker.bolt/close db))
