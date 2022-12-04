#! /udd/d/dbohdan/bin/joker

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

(defn cgi [env input]
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
       (prn-str
        (parse-query-default input))]
      (form (get env "SCRIPT_NAME" ""))]])))

(print
 (cgi
  (joker.os/env)
  (slurp *in*)))
