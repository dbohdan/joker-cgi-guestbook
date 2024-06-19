#! /arpa/af/d/dbohdan/bin/joker

(def db-file "guestbook.bolt")
(def entries-bucket "entries")
(def rate-limit-bucket "rate-limit")
(def rate-limit (* 24 60 60))

(defn parse-query [query]
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

(defn parse-query-default [query]
  (try
    (parse-query query)
    (catch Error e {:e e})))

(defn rate-limited? [db remote current-timestamp]
  (let [last-timestamp
        (->
          (joker.bolt/get db rate-limit-bucket remote)
          (or "0")
          (joker.strconv/parse-int 10 0))]
    (< (- current-timestamp last-timestamp) rate-limit)))

(defn add-record [db contact message name remote]
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
   [:dt "Name"] [:dd name]
   [:dt "Contact"] [:dd contact]
   [:dt "Message"] [:dd message]])

(defn entries [bucket-contents]
  [:div
   (for [[_ json] bucket-contents]
     [:article (entry (joker.json/read-string json))])])

(defn form [action]
  [:form {:method :post
          :action action}
   [:div
    [:label {:for :name} "Name:"]
    [:input {:type :text
             :id :name
             :name :name}]]
   [:div
    [:label {:for :contact} "Contact (will be public):"]
    [:input {:type :text
             :id :contact
             :name :contact}]]
   [:div
    [:label {:for :message} "Message:"]
    [:textarea {:name :message}]]
   [:div
    [:input {:type :submit}]]])

(defn cgi [db env input]
  (let [query (parse-query-default input)]
    (when (= (get env "REQUEST_METHOD" "") "POST")
      (let [remote (get env "REMOTE_HOST" (get env "REMOTE_ADDR" ""))]
        (when-not (rate-limited? db remote (unix-now))
          (add-record
           db
           (get query "contact" "")

           (get query "message" "")
           (get query "name" "")
           remote))))
    (str
     "Content-Type: text/html\r\n\r\n"
     "<!doctype html>"
     (joker.hiccup/html
      {:mode :html}
      [:html {:lang "en"}
       [:head
        [:title "Guestbook"]]
       [:body
        (entries
          (joker.bolt/by-prefix db entries-bucket ""))
        (form (get env "SCRIPT_NAME" ""))]]))))

(let [db (joker.bolt/open db-file 0600)]
  (joker.bolt/create-bucket-if-not-exists db entries-bucket)
  (joker.bolt/create-bucket-if-not-exists db rate-limit-bucket)
  (print
   (cgi
    db
    (joker.os/env)
    (slurp *in*)))
  (joker.bolt/close db))
