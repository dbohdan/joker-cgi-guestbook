#! /udd/d/dbohdan/bin/joker

(def db-file "guestbook.bolt")

(defn parse-query [query]
  (as-> query x
    (joker.string/split x "&")
    (mapcat
     #(rest (re-matches #"^([^=]*)=(.*)$" %))
     x)
    (map joker.url/query-unescape x)
    (apply hash-map x)))

(defn parse-query-default [query]
  (try
    (parse-query query)
    (catch Error e {:e e})))

(defn rate-limited? [remote] false)

(defn add-record [remote name contact message])

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
    (when (= (get query "REQUEST_METHOD" "") "POST")
      (let [remote (get env "REMOTE_HOST" (get env "REMOTE_ADDR" ""))]
        (when-not (rate-limited? remote)
          (add-record
           remote
           (get query "name" "")
           (get query "contact" "")
           (get query "message" "")))))
    (str
     "Content-Type: text/html\r\n\r\n"
     "<!doctype html>"
     (joker.hiccup/html
      {:mode :html}
      [:html {:lang "en"}
       [:head
        [:title "Joker CGI test"]]
       [:body
        [:code (prn-str env)]
        [:hr]
        [:code
         (prn-str query)]

        (form (get env "SCRIPT_NAME" ""))]]))))

(let [db (joker.bolt/open db-file 0600)]
  (joker.bolt/create-bucket-if-not-exists db "rate-limit")
  (joker.bolt/create-bucket-if-not-exists db "entries")
  (print
   (cgi
    db
    (joker.os/env)
    (slurp *in*)))
  (joker.bolt/close db))
