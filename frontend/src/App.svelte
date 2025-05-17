<script lang="ts">
  import { onMount } from "svelte";
  import nytLogo from "./assets/nyt.svg";
  import searchIcon from "./assets/search_icon.svg";

  console.log("Hello World!");

  // let apiKey: string = "default";

  const searchDefault: string = ""; //"davis";
  let searchTerm: string = searchDefault;
  let pagesLoaded: number = 0;
  // lock_scrollFetch is used to prevent the page from spamming fetch when the page scrolls. See init_scroll()
  let lock_scrollFetch: boolean = false;

  const scrollThreshold: number = 1000;

  // The articleID of the last article whose comments were opened
  let lastOpenedComments: string = "";

  // #region Initialization

  let email = "";
  onMount(async () => {
    const url = new URL(window.location.href);
    const em = url.searchParams.get("email");
    if (em) {
      email = em;
    }

    //console.log(email);
  });

  /**
   * Function to fetch API key and return it
   * provided by project starter code
   */
  /*export async function fetchKey(): Promise<string> {
    try {
      console.log("Fetching key...");
      const res = await fetch("/api/key");
      const data = await res.json();
      //apiKey = data.apiKey;
      //console.log(`API key fetched successfully: ${apiKey}`);
      console.log(`API key fetched successfully`);
      return data.apiKey;
    } catch (error) {
      console.error("Failed to fetch API key:", error);
      return "";
    }
  }*/

  /**
   * Intitialization function
   * Contains calls to functions that must run once the page loads
   */
  export async function load(): Promise<void> {
    console.log("Loaded yay!");
    displayDate();
    init_search_bar();
    init_scroll();
    // apiKey = await fetchKey();
    fetchAddArticles(2);
  }

  window.addEventListener("load", load); // calls the Intitialization function on page load

  /**
   * Initialize page scroll event detetction
   */
  export async function init_scroll(): Promise<void> {
    document.addEventListener("scroll", async (e: Event) => {
      // Inspired by https://medium.com/@alan.nguyen2050/detect-scroll-reaches-the-bottom-acb315824214

      // boolean for when the page has been scrolled beyond a certain threshold
      const reachedEnd =
        window.scrollY + window.innerHeight >=
        document.body.scrollHeight - scrollThreshold;
      //console.log(window.scrollY + window.innerHeight + "," + document.body.scrollHeight)

      if (reachedEnd && !lock_scrollFetch) {
        lock_scrollFetch = true; // prevent this block from running more than one at a time
        console.log("end of page reached");
        await fetchAddArticles(1);
        lock_scrollFetch = false;
      }
    });
  }

  /**
   * Initialize searchbar submission event detection
   */
  export async function init_search_bar(): Promise<void> {
    //console.log("setting up search bar")
    document
      .getElementById("search_bar")!
      .addEventListener("submit", function (e: SubmitEvent) {
        e.preventDefault();

        // Extraction of form contents inspired by https://stackoverflow.com/questions/37487826/send-form-data-to-javascript-on-submit
        //searchTerm = e.target.search_text_box.value

        let form = <HTMLElement>e.target!;
        let searchBar = <HTMLInputElement>form.children[0];
        searchTerm = searchBar.value;

        // if (searchTerm === "") {
        //   searchTerm = searchDefault;
        // }
        console.log("Submiting Search: " + searchTerm);
        clearArticles();
        fetchAddArticles(2);
      });
  }

  // #endregion Initialization

  // #region Article Fetching

  /**
   * Wrapper function to fetch (multiple) pages of articles.
   * Automatically tracks how many pages were fetched to avoid duplicates.
   * @param pages The number of pages to fetch.
   */
  export async function fetchAddArticles(pages: number): Promise<void> {
    console.log(`fetching ${pages} pages of articles`);
    //https://stackoverflow.com/questions/50924814/node-js-wait-for-multiple-async-calls-to-finish-before-continuing-in-code
    const promises = [];

    for (let i = 0; i < pages; i++) {
      promises.push(fetchData(pagesLoaded + 1));
      pagesLoaded++;
    }

    await Promise.all(promises);
    for (let i = 0; i < promises.length; i++) {
      processArticles(await promises[i]);
    }
    console.log("done");
  }
  /**
   * Generate a URL to fetch from The New York Times.
   * @param query
   * @param page
   * @param key
   * @returns
   */
  export function generateURL(
    query: string,
    page: number,
    // key: string,
  ): string {
    if (query) {
      // return `https://api.nytimes.com/svc/search/v2/articlesearch.json?q=${query}&api-key=${key}&page=${page}`;
      return `/api/articles-query/${page}/${query}`;
    } else {
      let fq = `timesTag.location:"Sacramento (Calif)" OR timesTag.location:"Davis (Calif)"`;
      // return `https://api.nytimes.com/svc/search/v2/articlesearch.json?fq=${fq.replace(":","%3A")}&api-key=${key}&page=${page}`;
      return `/api/articles-filter/${page}/${fq}`;
    }
  }

  export async function fetchData(page: number): Promise<Response> {
    console.log("Fetching data...");
    //console.log("API key: " + apiKey);
    try {
      let fetchResult = await fetch(generateURL(searchTerm, page /*, apiKey*/));
      console.log("Data received.");
      checkStatus(fetchResult);
      //console.log(await fetchResult.json())
      //console.log(JSON.stringify(await fetchResult.json()))
      //processArticles(await fetchResult.json());
      return await fetchResult.json();
    } catch (error) {
      errFunc(<Error>error);
    }
    /*
  fetch("https://api.nytimes.com/svc/search/v2/articlesearch.json?q=" + searchTerm + `&api-key=` + apiKey + "&page=" + page)
    .then(checkStatus)
    .then(Response => Response.json())
    .then(processArticles)
    .catch(errFunc)
  */
  }

  export function checkStatus(result: Response): Response {
    if (!result.ok) {
      throw Error;
    }
    return result;
  }

  export function errFunc(error: Error): void {
    console.log(error);
    console.log("An error has occured!");
  }

  export function processArticles(result: any): void {
    console.log(result);
    //console.log("Cool!")

    const srcList = result.response.docs;
    const feedGrid = document.getElementById("feed_grid")!;

    for (let i = 0; i < srcList.length; i++) {
      feedGrid.appendChild(createArticle(srcList[i]));
    }
  }

  /**
   * Removes all article tiles from the page
   */
  export function clearArticles(): void {
    const feedGrid = document.getElementById("feed_grid")!;
    while (feedGrid.children.length > 0) {
      feedGrid.children[0].remove();
    }
    pagesLoaded = 0;
  }

  /**
   * Create an article tile based on the template
   * @param srcArticle fetched source data
   * @returns HTML <article> with data filled in
   */
  export function createArticle(srcArticle: any): HTMLElement {
    const articleTemplate = (<HTMLTemplateElement>(
      document.getElementById("template_feed_item")!
    )).content.children[0];
    let newArticle = <HTMLElement>articleTemplate.cloneNode(true);
    let articleMain = <HTMLLinkElement>newArticle.children[0];
    articleMain.href = srcArticle.web_url;

    // feed_title
    articleMain.children[1].textContent = srcArticle.headline.main;

    // feed_main
    articleMain.children[2].textContent = srcArticle.snippet;

    // words
    //articleMain.children[3].textContent = calcReadTime(srcArticle.word_count) + " MIN READ";
    {
      let readtime = <HTMLLinkElement>newArticle.children[1].children[0];
      readtime.textContent = calcReadTime(srcArticle.word_count) + " MIN READ";
      readtime.href = srcArticle.web_url;
    }
    {
      let button = <HTMLButtonElement>newArticle.children[1].children[1];
      button.onclick = openComments;

      const idTrim = "/";
      const sections = srcArticle._id.split(idTrim);
      button.children[0].textContent = sections[sections.length - 1];
    }

    // feed_thumbnail
    {
      let feed_thumbnail = articleMain.children[0];
      let caption = feed_thumbnail.children[1];
      let image = <HTMLImageElement>feed_thumbnail.children[0];
      caption.textContent = srcArticle.multimedia.credit;
      image.src = srcArticle.multimedia.default.url;
      image.alt = srcArticle.multimedia.caption;
    }

    return newArticle;
  }

  /**
   * Function that converts the number of words to how many minutes it may take to read
   * @param word_count Number of words in an article
   * @returns Approximately how long it may take to read that article
   */
  export function calcReadTime(word_count: number): number {
    const average_words_per_minute = 175;
    return Math.max(Math.ceil(word_count / average_words_per_minute), 1);
  }

  // #endregion Article Fetching

  // #region Date Stuff

  export function displayDate(): void {
    const date = new Date();
    //console.log(document.getElementById("header_date_date").textContent)
    document.getElementById("header_date_date")!.textContent = dateStr(date);
    //console.log(document.getElementById("header_date_date").textContent)
  }

  /**
   * Convert numerical month index to month name as a string
   * @param {number} index - The index of the month to convert (0 to 11)
   * @returns {string} The name of the month
   */
  export function monthStr(index: number): string {
    const months = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ];
    return months[index];
  }

  /**
   * Convert numerical weekday index to day name as a string
   * @param {number} index - The index of the weekday to convert (0 to 6)
   * @returns {string} The name of the weekday
   */
  export function weekStr(index: number): string {
    const days = [
      "Sunday",
      "Monday",
      "Tuesday",
      "Wednesday",
      "Thursday",
      "Friday",
      "Saturday",
    ];
    return days[index];
  }

  /**
   * Convert date object to string
   * @param {Date} date - Date to convert
   * @returns {string} The date as a string
   */
  export function dateStr(date: Date): string {
    let ret = "";
    ret = weekStr(date.getDay()) + ", ";
    ret += monthStr(date.getMonth()) + " ";
    ret += date.getDate() + ", ";
    ret += date.getFullYear();
    return ret;
  }

  // #endregion Date Stuff

  // #region Comments

  function redirectToLogin() {
    window.location.href = "http://localhost:8000/login";
  }
  async function BUTTON() {
    window.location.href = "http://localhost:8000/login";
    return;
    try {
      console.log("BUTTON");
      const res = await fetch("/login");
      const data = await res.json();
      console.log(data);
    } catch (error) {
      console.error("data.AAAAAAA: ", error);
      return "";
    }
  }

  function renderComment(
    commentTemplate: HTMLElement,
    commentJson: any,
    articleID: string,
    replyTemplate: HTMLElement,
  ): HTMLElement {
    let newComment = <HTMLElement>commentTemplate.cloneNode(true);

    //comment_username
    newComment.children[0].textContent = commentJson.username;

    //comment_body
    newComment.children[1].textContent = commentJson.content;

    //reply_form
    {
      let form = <HTMLFormElement>newComment.children[3];
      form.addEventListener("submit", postReply);
      form.children[2].textContent = articleID;
      form.children[3].textContent = commentJson._id;
    }

    //comment_replies
    {
      let replyList = newComment.children[2];
      for (let index = 0; index < commentJson.replies.length; index++) {
        const replyJson = commentJson.replies[index];
        replyList.appendChild(renderReply(replyTemplate, replyJson));
      }
    }

    return newComment;
  }

  function renderReply(
    replyTemplate: HTMLElement,
    replyJson: any,
  ): HTMLElement {
    let newReply = <HTMLElement>replyTemplate.cloneNode(true);
    //reply_username
    newReply.children[0].textContent = replyJson.username;

    //commentreply_body_body
    newReply.children[1].textContent = replyJson.content;
    return newReply;
  }

  async function openComments(this: HTMLButtonElement) {
    const articleID = this.children[0].textContent!;

    console.log("openComments: " + articleID);

    //https://www.w3schools.com/howto/tryit.asp?filename=tryhow_js_sidenav
    let comments_panel = document.getElementById("comments_panel")!;
    comments_panel.style.width = "250px";
    if (lastOpenedComments === articleID) {
      // don't rerender comments
    } else {
      lastOpenedComments = articleID;
      
      const comments_list = document.getElementById("comments_list")!;
      while (comments_list.children.length > 0) {
        comments_list.children[0].remove();
      }

      let comments = null;
      try {
        const res = await fetch(`/api/comments/${articleID}`);
        const data = await res.json();
        console.log(data);
        comments = data.comments;
      } catch (error) {
        console.error("error: ", error);
        comments_list.textContent = "Failed to load comments";
        return;
      }

      const commentTemplate = <HTMLElement>(
        (<HTMLTemplateElement>document.getElementById("template_comment")!)
          .content.children[0]
      );
      const replyTemplate = <HTMLElement>(
        (<HTMLTemplateElement>document.getElementById("template_reply")!)
          .content.children[0]
      );

      for (let index = 0; index < comments.length; index++) {
        comments_list.appendChild(
          renderComment(
            commentTemplate,
            comments[index],
            articleID,
            replyTemplate,
          ),
        );
      }

      comments_panel.children[0].textContent = articleID;
    }
  }
  async function closeComments() {
    document.getElementById("comments_panel")!.style.width = "0px";
  }

  async function postCommentCall(
    articleID: string,
    parentID: string,
    content: string,
  ) {
    try {
      let data = new FormData();
      data.append("articleID", articleID);
      data.append("parentID", parentID);
      data.append("email", email);
      data.append("content", content);

      await fetch("/api/postcomment", {
        method: "POST",
        body: data,
      });
    } catch (error) {
      console.log("Failed to post reply.");
    }
  }
  async function postReply(e: SubmitEvent) {
    e.preventDefault();
    if (!email) {
      redirectToLogin();
      return;
    }

    const form = <HTMLElement>e.target!;
    const reply_box = <HTMLInputElement>form.children[0];
    const reply_body = reply_box.value;

    const articleID = form.children[2].textContent!;
    const commentID = form.children[3].textContent!;
    postCommentCall(articleID, commentID, reply_body);
    //console.log(reply_body);
  }
  // #endregion Comments
</script>

<main>
  <!--The New York Times front page mock-up made by Ellison Song and Sean Singleton
  Ellison Song: ellsong@ucdavis.edu
  Sean Singleton: ssingleton@ucdavis.edu

  SVG sources linked in HTML comments or in .svg file comments.
  
  No AI was used in the production of this project.-->
  <header>
    <section class="header_flex">
      <h1 hidden>The New York Times</h1>

      <div id="header_date">
        <p id="header_date_date">
          Today's date. This should be replaced via JS code.
        </p>
        <p id="header_date_tagline">Today's Paper</p>
      </div>

      <div id="logo_nyt">
        <!--The NYT logo is, in fact, not actually text displayed with a font. Instead, it is a piece of vector art hard-coded entirely in HTML. As such, the path element and its svg's viewbox attribute have been copied here. This is the only html that has been copied from an external site.-->
        <!--SVG source: https://www.nytimes.com/-->
        <img src={nytLogo} alt="The New York Times" />
      </div>

      <div id="header_search">
        <form id="search_bar">
          <input id="search_text_box" type="text" />
          <button id="search_button">
            <!--The seach icon is also an SVG.-->
            <!--SVG source: https://www.nytimes.com/-->
            <img src={searchIcon} alt="Search" />
          </button>
        </form>
      </div>
    </section>
    <div class="line_horizontal_double"></div>
  </header>

  <button onclick={BUTTON}>BUTTON</button>

  <section id="comments_panel">
    <h1 hidden>Comments Pannel</h1>
    <div>
      <button id="comments_panel_closebutton" onclick={closeComments}>
        close
      </button>
      {#if email}
        <p>{email}</p>
      {:else}
        <button onclick={redirectToLogin}>Login</button>
      {/if}
    </div>
    <section id="comments_list">
      <h1>Comments</h1>
      <!-- Commnets go here! -->
    </section>
  </section>

  <section id="feed_grid">
    <h1 hidden>Articles</h1>
    <!--Concrete articles go here!-->
  </section>

  <template id="template_feed_item">
    <article>
      <a class="feed_item" href="">
        <figure class="feed_thumbnail">
          <img src="" alt="The thumbnail for the article" />
          <figcaption>
            The caption for the thumbnail for the article that displays the
            image's credits.
          </figcaption>
        </figure>

        <h2 class="feed_title">Feed_Title</h2>

        <p class="feed_main">Feed_Main</p>
      </a>
      <div>
        <a class="feed_readtime">
          The read time, as calculated from word count.
        </a>
        <button>
          Comments
          <p hidden>article ID</p>
        </button>
      </div>
      <div class="line_horizontal"></div>
    </article>
  </template>

  <template id="template_comment">
    <div class="comment">
      <p class="comment_username">Commenter Username</p>
      <p class="comment_body">Comment Body</p>
      <section class="comment_replies">
        <h1>Replies</h1>
        <!-- replies go here -->
      </section>
      <form class="reply_form">
        <input class="reply_textbox" type="text" />
        <button class="reply_submit">Post</button>
        <p hidden>ARTICLE_ID</p>
        <p hidden>COMMENT_ID</p>
      </form>
    </div>
  </template>

  <template id="template_reply">
    <div class="reply">
      <p class="reply_username">Replier Username</p>
      <p class="reply_body">Repy Body</p>
    </div>
  </template>
</main>

<style>
  /* #region Comments */
  /*https://www.w3schools.com/howto/tryit.asp?filename=tryhow_js_sidenav*/
  #comments_panel {
    height: 100%;
    width: 0;
    position: fixed;
    z-index: 1;
    top: 0;
    right: 0;
    background-color: #dfdfdf;
    /* overflow-x: hidden; */
    overflow-y: scroll;
    transition: 0.5s;
    padding: 20px;
  }
  .comment {
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 12px;
    color: black;
  }
  .comment_replies > h1 {
    text-align: left;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: small;
    color: grey;
  }

  .reply_from {
    display: flex;
    flex-direction: row;
    .reply_textbox {
      width: 90%;
      height: 20px;
    }
    .reply_submit {
      width: 20px;
      height: 20px;
    }
  }

  /* #endregion Comments */

  /* #region Header */
  /*set the max page width*/
  header,
  body {
    max-width: 1500px;
    margin: auto;
  }

  /*header fomatting*/
  .header_flex {
    display: flex;
    justify-content: space-between;
  }

  .header_flex > div {
    width: 100%;
    padding: 10px;
  }

  /*fomatting for the main logo*/
  #logo_nyt {
    width: 100%;
    min-width: 290px;
  }

  /*fomatting for the date*/
  #header_date {
    display: flex;
    flex-direction: column;
    justify-content: center;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    padding-left: 10px;

    p {
      margin: 0px;
      text-align: left;
    }
  }

  #header_search {
    display: flex;
    justify-content: end;
    align-items: center;
    width: 100%;
  }

  #search_button {
    width: 16px;
    margin: 0px;
    padding: 0px;
  }

  /* #endregion Header */

  /* #region Feed Grid */

  /*horizontal lines*/
  .line_horizontal {
    border-style: solid;
    border-color: #dfdfdf;
    border-width: 0px 0px 2px 0px;
  }

  .line_horizontal_double {
    height: 2px;

    border-style: solid;
    border-color: black;
    border-width: 1px 0px 1px 0px;
  }

  /*main article pages grid*/
  #feed_grid {
    margin: 10px;

    display: grid;
    flex-direction: column;
    grid-template-columns: repeat(3, 1fr);

    border-style: solid;
    border-color: #dfdfdf;
    border-width: 0px 0px 0px 2px;

    font-family: Georgia;
  }

  /*media queries to change the number of columns based on page width
Based on examples by w3schools's Media Queries tutorial: https://www.w3schools.com/css/css_rwd_mediaqueries.asp
*/
  @media only screen and (max-width: 1024px) {
    #feed_grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media only screen and (max-width: 768px) {
    #feed_grid {
      grid-template-columns: 100%;
    }

    /*these rearrange the header so that the logo does not cause the date to wrap*/
    .header_flex {
      flex-direction: column;
      align-items: center;
    }

    #header_date {
      padding-left: 30px;
      padding-top: 13.5px;
    }

    #logo_nyt {
      max-width: 290px;
      margin: 0px;
      padding: 0px;
    }
  }

  /*general item format*/
  #feed_grid > .feed_item {
    margin: 0px;
    padding: 10px;

    border-style: solid;
    border-color: #dfdfdf;
    border-width: 0px 2px 0px 0px;

    display: block;
  }

  /*formatting for clickable articles*/
  a.feed_item:link {
    color: black;
    text-decoration: none;
  }

  /*formatting for image container*/
  .feed_thumbnail {
    margin: 5px;
  }

  /*formatting for image caption*/
  .feed_thumbnail > figcaption {
    margin: 1px;
    padding-top: 5px;
    padding-right: 10px;

    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    text-align: right;
    font-size: 12px;
    letter-spacing: 0.01px;
    color: #5a5a5a;
  }

  /*formatting for the image*/
  .feed_thumbnail > img {
    display: block;
    margin: auto;
    width: 100%;
    height: auto;
    object-fit: contain;
  }

  /*formatting for the little 'LIVE' indicator above some articles*/
  .feed_live {
    padding: 0px 10px;
    margin: 0px;
    font-size: x-small;
    font-weight: bold;
    color: red;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    letter-spacing: 1px;
  }

  /*formatting for the article titles*/
  .feed_title {
    font-size: larger;
    margin-top: 5px;
    margin-bottom: 5px;
    padding: 0px 10px;
    text-align: left;
    font-weight: bold;
  }

  /*formatting for the article content*/
  .feed_main {
    font-size: small;
    color: #5a5a5a;
    padding: 0px 10px 0px 10px;
    text-align: left;
    line-height: 20px;
  }

  /*formatting for the list that appears in some articles' content*/
  .feed_main_list {
    font-size: small;
    color: #5a5a5a;
    line-height: 20px;
  }

  /*formatting for the little read length indicator*/
  .feed_readtime {
    font-size: x-small;
    color: #727272;
    padding: 0px 10px 10px 10px;
    margin: 0px;
    text-align: left;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    letter-spacing: 0.5px;
  }
  /* #region Feed Grid */
</style>
