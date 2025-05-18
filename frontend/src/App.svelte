<script lang="ts">
  // #region Script
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
  let userPermissions: any = {};
  onMount(async () => {
    const url = new URL(window.location.href);
    const em = url.searchParams.get("email");
    if (em) {
      email = em;
    }
    try {
      let fetchResult = await fetch(`/api/checkpermissions/${email}`);
      userPermissions = await fetchResult.json();
    } catch (error) {
      console.log("Failed to fetch permissions: " + error);
    }
    console.log(userPermissions);
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

  // json object containing indexes for html elements
  const COMMENT_STRUCT = {
    PANEL: {
      comments_panel_header: 1,
      comment_form: 2,
      comments_list: 3,
      COMMENT_FORM: {
        comment_textbox: 0,
        comment_submit: 1,
        article_id: 2,
      },
    },
    COMMENT: {
      article_id: 0,
      comment_id: 1,
      comment_username: 2,
      comment_body: 3,
      comment_body_textarea: 4,
      mod_actions: 5,
      comment_replies: 6,
      reply_form: 7,
      line_horizontal: 8,
      MOD_ACTIONS: {
        mod_actions_directions: 0,
        button_remove: 1,
        button_redact: 2,
        button_remove_confirm: 3,
        button_remove_cancel: 4,
        button_redact_confirm: 5,
        button_redact_cancel: 6,
      },
      REPLY_FORM: {
        reply_textbox: 0,
        reply_submit: 1,
      },
    },
    REPLY: {
      reply_id: 0,
      reply_username: 1,
      reply_body: 2,
      reply_body_textarea: 3,
      mod_actions: 4,
      MOD_ACTIONS: {
        mod_actions_directions: 0,
        button_remove: 1,
        button_redact: 2,
        button_remove_confirm: 3,
        button_remove_cancel: 4,
        button_redact_confirm: 5,
        button_redact_cancel: 6,
      },
    },
  };
  /**
   *
   */
  function redirectToLogin() {
    window.location.href = "http://localhost:8000/login";
  }

  // #region Render
  function renderComment(
    commentTemplate: HTMLElement,
    commentJson: any,
    articleID: string,
    replyTemplate: HTMLElement,
  ): HTMLElement {
    let newComment = <HTMLElement>commentTemplate.cloneNode(true);

    //article_id
    newComment.children[COMMENT_STRUCT.COMMENT.article_id].textContent =
      articleID;
    //comment_id
    newComment.children[COMMENT_STRUCT.COMMENT.comment_id].textContent =
      commentJson._id;

    //comment_username
    newComment.children[COMMENT_STRUCT.COMMENT.comment_username].textContent =
      commentJson.username;

    //comment_body
    newComment.children[COMMENT_STRUCT.COMMENT.comment_body].textContent =
      commentJson.content;

    //mod_actions
    {
      if (userPermissions.can_remove_comments && !commentJson.removed) {
        const mod_actions = <HTMLDivElement>(
          newComment.children[COMMENT_STRUCT.COMMENT.mod_actions]
        );
        mod_actions.hidden = false;
        function setButton(key: string, callback: Function) {
          (<HTMLButtonElement>(
            mod_actions.children[COMMENT_STRUCT.COMMENT.MOD_ACTIONS[key]]
          )).onclick = callback;
        }
        setButton("button_remove", callback_button_remove);
        setButton("button_remove_confirm", callback_button_remove_confirm);
        setButton("button_remove_cancel", callback_button_remove_cancel);
        setButton("button_redact", callback_button_redact);
        setButton("button_redact_confirm", callback_button_redact_confirm);
        setButton("button_redact_cancel", callback_button_redact_cancel);
      }
    }

    //reply_form
    {
      let form = <HTMLFormElement>(
        newComment.children[COMMENT_STRUCT.COMMENT.reply_form]
      );
      form.addEventListener("submit", postReply);
    }

    //comment_replies
    {
      let replyList =
        newComment.children[COMMENT_STRUCT.COMMENT.comment_replies];
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

    //reply_id
    newReply.children[COMMENT_STRUCT.REPLY.reply_id].textContent =
      replyJson._id;

    //reply_username
    newReply.children[COMMENT_STRUCT.REPLY.reply_username].textContent =
      replyJson.username;

    //reply_body
    newReply.children[COMMENT_STRUCT.REPLY.reply_body].textContent =
      replyJson.content;

    //mod_actions
    {
      if (userPermissions.can_remove_comments && !replyJson.removed) {
        const mod_actions = <HTMLDivElement>(
          newReply.children[COMMENT_STRUCT.REPLY.mod_actions]
        );
        mod_actions.hidden = false;
        function setButton(key: string, callback: Function) {
          (<HTMLButtonElement>(
            mod_actions.children[COMMENT_STRUCT.COMMENT.MOD_ACTIONS[key]]
          )).onclick = callback;
        }
        setButton("button_remove", callback_button_remove);
        setButton("button_remove_confirm", callback_button_remove_confirm);
        setButton("button_remove_cancel", callback_button_remove_cancel);
        setButton("button_redact", callback_button_redact);
        setButton("button_redact_confirm", callback_button_redact_confirm);
        setButton("button_redact_cancel", callback_button_redact_cancel);
      }
    }

    return newReply;
  }

  function getTemplate(template_name_id: string) {
    return <HTMLElement>(
      (<HTMLTemplateElement>document.getElementById(template_name_id)!).content
        .children[0]
    );
  }
  // #endregion Render

  // #region Panel Mechanics
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

      //comment_form
      {
        let form = <HTMLFormElement>comments_panel.children[2];
        form.addEventListener("submit", postComment);
        form.children[2].textContent = articleID;
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

      const commentTemplate = getTemplate("template_comment");
      const replyTemplate = getTemplate("template_reply");

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
  // #endregion Panel Mechanics

  // #region Post Mechanics
  async function postCommentCall(
    articleID: string,
    parentID: string,
    content: string,
  ): Promise<any | null> {
    if (content.trim().length == 0) {
      return null;
    }

    try {
      let data = new FormData();
      data.append("articleID", articleID);
      data.append("parentID", parentID);
      data.append("email", email);
      data.append("content", content);

      const res = await fetch("/api/postcomment", {
        method: "POST",
        body: data,
      });
      const res_data = await res.json();
      console.log(res_data);

      return res_data;
    } catch (error) {
      console.log("Failed to post comment: " + error);
      return null;
    }
  }
  async function removeCommentCall(commentID: string) {
    try {
      let data = new FormData();
      data.append("commentID", commentID);

      const res = await fetch("/api/removecomment", {
        method: "POST",
        body: data,
      });
      const res_data = await res.json();
      console.log(res_data);

      return res_data;
    } catch (error) {
      console.log("Failed to remove comment: " + error);
      return null;
    }
  }
  async function redactCommentCall(
    commentID: string,
    startIndex: number,
    endIndex: number,
  ) {
    try {
      let data = new FormData();
      data.append("commentID", commentID);
      data.append("startIndex", startIndex.toString());
      data.append("endIndex", endIndex.toString());

      const res = await fetch("/api/redactcomment", {
        method: "POST",
        body: data,
      });
      const res_data = await res.json();
      console.log(res_data);

      return res_data;
    } catch (error) {
      console.log("Failed to redact comment: " + error);
      return null;
    }
  }
  async function postReply(e: SubmitEvent) {
    e.preventDefault();
    if (!email) {
      redirectToLogin();
      return;
    }

    const form = <HTMLElement>e.target!;
    const reply_box = <HTMLInputElement>(
      form.children[COMMENT_STRUCT.COMMENT.REPLY_FORM.reply_textbox]
    );
    const reply_body = reply_box.value;

    const parentComment = form.parentElement!;

    const articleID =
      parentComment.children[COMMENT_STRUCT.COMMENT.article_id].textContent!;
    const parentID =
      parentComment.children[COMMENT_STRUCT.COMMENT.comment_id].textContent!;

    const newCommentData = await postCommentCall(
      articleID,
      parentID,
      reply_body,
    );
    if (newCommentData != null) {
      const newCommentJson = newCommentData.commentData; //await newCommentData.json();

      const existing_replies_list =
        parentComment.children[COMMENT_STRUCT.COMMENT.comment_replies]!;
      existing_replies_list.appendChild(
        renderReply(getTemplate("template_reply"), newCommentJson),
      );
      reply_box.value = "";
    }
  }
  async function postComment(e: SubmitEvent) {
    e.preventDefault();
    if (!email) {
      redirectToLogin();
      return;
    }

    const form = <HTMLElement>e.target!;
    const comment_box = <HTMLInputElement>(
      form.children[COMMENT_STRUCT.PANEL.COMMENT_FORM.comment_textbox]
    );
    const comment_body = comment_box.value;

    const articleID =
      form.children[COMMENT_STRUCT.PANEL.COMMENT_FORM.article_id].textContent!;

    const newCommentData = await postCommentCall(articleID, "", comment_body);
    if (newCommentData != null) {
      const newCommentJson = newCommentData.commentData; //await newCommentData.json();

      const existing_comments_list =
        form.parentElement!.children[COMMENT_STRUCT.PANEL.comments_list]!;
      existing_comments_list.insertBefore(
        renderComment(
          getTemplate("template_comment"),
          newCommentJson,
          articleID,
          getTemplate("template_reply"),
        ),
        existing_comments_list.firstChild,
      );
      comment_box.value = "";
    }
  }

  // #region Mod Actions
  const MOD_ACTIONS_ARRANGEMENT = {
    idle: {
      mod_actions_directions: "",
      button_remove: true,
      button_redact: true,
      button_remove_confirm: false,
      button_remove_cancel: false,
      button_redact_confirm: false,
      button_redact_cancel: false,
    },
    removing: {
      mod_actions_directions: "Remove comment?",
      button_remove: false,
      button_redact: false,
      button_remove_confirm: true,
      button_remove_cancel: true,
      button_redact_confirm: false,
      button_redact_cancel: false,
    },
    redacting: {
      mod_actions_directions: "Select text to redact",
      button_remove: false,
      button_redact: false,
      button_remove_confirm: false,
      button_remove_cancel: false,
      button_redact_confirm: true,
      button_redact_cancel: true,
    },
    removed: {
      mod_actions_directions: "",
      button_remove: false,
      button_redact: false,
      button_remove_confirm: false,
      button_remove_cancel: false,
      button_redact_confirm: false,
      button_redact_cancel: false,
    },
  };
  function arrange_mod_actions(
    mod_actions: HTMLDivElement,
    structure: any,
    arrangement: any,
  ) {
    mod_actions.children[structure.mod_actions_directions].textContent =
      arrangement.mod_actions_directions;

    const buttons = [
      "button_remove",
      "button_redact",
      "button_remove_confirm",
      "button_remove_cancel",
      "button_redact_confirm",
      "button_redact_cancel",
    ];
    buttons.forEach((button: string) => {
      (<HTMLButtonElement>mod_actions.children[structure[button]]).hidden =
        !arrangement[button];
    });
  }

  async function callback_button_remove(this: HTMLButtonElement) {
    const mod_actions = <HTMLDivElement>this.parentElement!;
    const thisComment = <HTMLDivElement>mod_actions.parentElement!;
    let structure = COMMENT_STRUCT.COMMENT.MOD_ACTIONS;
    if (thisComment.classList.contains("reply")) {
      structure = COMMENT_STRUCT.REPLY.MOD_ACTIONS;
    }
    arrange_mod_actions(
      mod_actions,
      structure,
      MOD_ACTIONS_ARRANGEMENT.removing,
    );
  }
  async function callback_button_remove_confirm(this: HTMLButtonElement) {
    const mod_actions = <HTMLDivElement>this.parentElement!;
    const thisComment = <HTMLDivElement>mod_actions.parentElement!;
    let structure = COMMENT_STRUCT.COMMENT.MOD_ACTIONS;
    let struct_id = COMMENT_STRUCT.COMMENT.comment_id;
    let struct_body = COMMENT_STRUCT.COMMENT.comment_body;
    if (thisComment.classList.contains("reply")) {
      structure = COMMENT_STRUCT.REPLY.MOD_ACTIONS;
      struct_id = COMMENT_STRUCT.REPLY.reply_id;
      struct_body = COMMENT_STRUCT.REPLY.reply_body;
    }
    arrange_mod_actions(
      mod_actions,
      structure,
      MOD_ACTIONS_ARRANGEMENT.removed,
    );

    const commentID = thisComment.children[struct_id].textContent!;

    const newCommentData = await removeCommentCall(commentID);
    const newCommentJson = newCommentData.commentData;

    thisComment.children[struct_body].textContent = newCommentJson.content;
  }
  async function callback_button_remove_cancel(this: HTMLButtonElement) {
    const mod_actions = <HTMLDivElement>this.parentElement!;
    const thisComment = <HTMLDivElement>mod_actions.parentElement!;
    let structure = COMMENT_STRUCT.COMMENT.MOD_ACTIONS;
    if (thisComment.classList.contains("reply")) {
      structure = COMMENT_STRUCT.REPLY.MOD_ACTIONS;
    }
    arrange_mod_actions(mod_actions, structure, MOD_ACTIONS_ARRANGEMENT.idle);
  }

  async function callback_button_redact(this: HTMLButtonElement) {
    const mod_actions = <HTMLDivElement>this.parentElement!;
    const thisComment = <HTMLDivElement>mod_actions.parentElement!;
    let structure = COMMENT_STRUCT.COMMENT.MOD_ACTIONS;
    let struct_body = COMMENT_STRUCT.COMMENT.comment_body;
    let struct_textarea = COMMENT_STRUCT.COMMENT.comment_body_textarea;
    if (thisComment.classList.contains("reply")) {
      structure = COMMENT_STRUCT.REPLY.MOD_ACTIONS;
      struct_body = COMMENT_STRUCT.REPLY.reply_body;
      struct_textarea = COMMENT_STRUCT.REPLY.reply_body_textarea;
    }
    arrange_mod_actions(
      mod_actions,
      structure,
      MOD_ACTIONS_ARRANGEMENT.redacting,
    );

    const body = <HTMLParagraphElement>thisComment.children[struct_body];
    const textarea = <HTMLTextAreaElement>thisComment.children[struct_textarea];

    body.hidden = true;
    textarea.hidden = false;
    textarea.textContent = body.textContent;
  }
  async function callback_button_redact_confirm(this: HTMLButtonElement) {
    const mod_actions = <HTMLDivElement>this.parentElement!;
    const thisComment = <HTMLDivElement>mod_actions.parentElement!;
    let structure = COMMENT_STRUCT.COMMENT.MOD_ACTIONS;
    let struct_id = COMMENT_STRUCT.COMMENT.comment_id;
    let struct_textarea = COMMENT_STRUCT.COMMENT.comment_body_textarea;
    if (thisComment.classList.contains("reply")) {
      structure = COMMENT_STRUCT.REPLY.MOD_ACTIONS;
      struct_id = COMMENT_STRUCT.REPLY.reply_id;
      struct_textarea = COMMENT_STRUCT.REPLY.reply_body_textarea;
    }
    const textarea = <HTMLTextAreaElement>(
      thisComment.children[struct_textarea]!
    );
    const sStart = textarea.selectionStart;
    const sEnd = textarea.selectionEnd;
    console.log(textarea.textContent!.slice(sStart, sEnd));

    const commentID = thisComment.children[struct_id].textContent!;

    const newCommentData = await redactCommentCall(commentID, sStart, sEnd);
    const newCommentJson = newCommentData.commentData;

    thisComment.children[struct_textarea].textContent = newCommentJson.content;
  }
  async function callback_button_redact_cancel(this: HTMLButtonElement) {
    const mod_actions = <HTMLDivElement>this.parentElement!;
    const thisComment = <HTMLDivElement>mod_actions.parentElement!;
    let structure = COMMENT_STRUCT.COMMENT.MOD_ACTIONS;
    let struct_body = COMMENT_STRUCT.COMMENT.comment_body;
    let struct_textarea = COMMENT_STRUCT.COMMENT.comment_body_textarea;
    if (thisComment.classList.contains("reply")) {
      structure = COMMENT_STRUCT.REPLY.MOD_ACTIONS;
      struct_body = COMMENT_STRUCT.REPLY.reply_body;
      struct_textarea = COMMENT_STRUCT.REPLY.reply_body_textarea;
    }
    arrange_mod_actions(mod_actions, structure, MOD_ACTIONS_ARRANGEMENT.idle);

    const body = <HTMLParagraphElement>thisComment.children[struct_body];
    const textarea = <HTMLTextAreaElement>thisComment.children[struct_textarea];

    textarea.hidden = true;
    body.hidden = false;
    body.textContent = textarea.textContent;
  }

  // #endregion Mod Actions

  // #endregion Post Mechanics
  // #endregion Comments
  // #endregion Script
</script>

<main>
  <!-- #region HTML -->
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

  <section id="comments_panel">
    <h1 hidden>Comments Pannel</h1>
    <div id="comments_panel_header">
      <button id="comments_panel_closebutton" onclick={closeComments}>
        close
      </button>
      {#if email}
        <p>{email}</p>
      {:else}
        <button onclick={redirectToLogin}>Login</button>
      {/if}
    </div>
    <form class="comment_form">
      <input class="comment_textbox" type="text" />
      <button class="comment_submit">Post</button>
      <p hidden>ARTICLE_ID</p>
    </form>
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
      <p hidden>ARTICLE_ID</p>
      <p hidden>COMMENT_ID</p>
      <p class="comment_username">Commenter Username</p>
      <p class="comment_body">Comment Body</p>
      <textarea hidden readonly class="comment_body">Comment Body</textarea>
      <div class="mod_actions" hidden>
        <p class="mod_actions_directions"></p>
        <button class="button_remove">Remove</button>
        <button class="button_redact">Redact</button>
        <button class="button_remove_confirm" hidden>Yes</button>
        <button class="button_remove_cancel" hidden>No</button>
        <button class="button_redact_confirm" hidden>Redact</button>
        <button class="button_redact_cancel" hidden>Done</button>
      </div>
      <section class="comment_replies">
        <h1>Replies</h1>
        <!-- replies go here -->
      </section>
      <form class="reply_form">
        <input class="reply_textbox" type="text" />
        <button class="reply_submit">Post</button>
      </form>
      <div class="line_horizontal"></div>
    </div>
  </template>

  <template id="template_reply">
    <div class="reply">
      <p hidden>REPLY_ID</p>
      <p class="reply_username">Replier Username</p>
      <p class="reply_body">Reply Body</p>
      <textarea hidden readonly class="reply_body">Reply Body</textarea>
      <div class="mod_actions" hidden>
        <p class="mod_actions_directions"></p>
        <button class="button_remove">Remove</button>
        <button class="button_redact">Redact</button>
        <button class="button_remove_confirm" hidden>Yes</button>
        <button class="button_remove_cancel" hidden>No</button>
        <button class="button_redact_confirm" hidden>Redact</button>
        <button class="button_redact_cancel" hidden>Done</button>
      </div>
    </div>
  </template>
  <!-- #endregion HTML -->
</main>

<style>
  /* #region Style */

  /* #region Comments */
  /*https://www.w3schools.com/howto/tryit.asp?filename=tryhow_js_sidenav*/
  #comments_panel {
    height: 100svh;
    width: 0;
    position: -webkit-sticky;
    position: fixed;
    z-index: 1;
    top: 0;
    right: 0;
    background-color: #dfdfdf;
    overflow-y: auto;
    transition: 0.5s;
    margin: 0;

    div,
    section {
      padding: 5px;
    }
  }

  .comment,
  .reply {
    text-align: left;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: medium;
    color: black;
    margin: 0;
    border: 0;

    .comment_username,
    .reply_username {
      margin: 0;
      padding: 1px;
    }
    .comment_body,
    .reply_body {
      font-size: small;
      margin: 0;
      padding: 1px 3px 1px 1px;
    }
    .line_horizontal {
      border-color: grey;
      border-width: 0px 0px 1px 0px;
    }
  }
  .mod_actions > button {
    font-size: small;
  }
  .comment_replies > h1 {
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: small;
    color: grey;
  }

  .comment_from,
  .reply_from {
    display: flex;
    flex-direction: row;
  }
  .comment_textbox,
  .reply_textbox {
    flex-grow: 1;
    height: 20px;
    padding: 2px;
    border-width: 1px;
  }
  .comment_submit,
  .reply_submit {
    flex-grow: 1;
    height: 27.2px;
    padding: 2px;
    border-width: 1px;
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
  /* #endregion Feed Grid */
  /* #endregion Style */
</style>
