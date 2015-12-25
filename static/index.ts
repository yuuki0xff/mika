/// <reference path="./typings/jquery/jquery.d.ts" />
/// <reference path="./typings/angularjs/angular.d.ts" />
/// <reference path="./typings/angular-material/angular-material.d.ts" />
/// <reference path="./lib/sanitize.d.ts" />

module Security{
	export interface Sanitizer{
		clean_string(s:string): string;
	}

	export class RecordSanitizer implements Sanitizer{
		sanitizer: any;
		domParser: any;

		constructor(private $sce){
			var config = {
				elements: "br".split(" "),
			};
			this.sanitizer = new Sanitize(config);
			this.domParser = new DOMParser();
		}

		clean_string(s:string): string{
			var dirtyDom = this.domParser.parseFromString(s, "text/html");
			var cleanNode = this.sanitizer.clean_node(dirtyDom);
			var cleanDom = document.implementation.createHTMLDocument("");
			cleanDom.body.appendChild(cleanNode);
			return this.$sce.trustAsHtml(cleanDom.body.innerHTML);
		}
	}
}

module API{
	/****************************************************************
 	 * 列挙型
	 * errorType
	 *
	 * インタフェース
	 * IAjaxCallback
	 *
	 * 関数
	 * ajax
	 *
	 * クラス
	 * Threads
	 * Records
	 * Attach
	****************************************************************/
	var baseURL:string = window.location.pathname.split("/").slice(0,-1).join("/") + "/api/v0.1";

	export enum errorType{
		"timeout",
		"error",
		"notmodified",
		"parsererror",
	}

	export interface IAjaxCallback{
		success:(any)=>any;
		error:(errorType)=>any;
	}

	// ajax通信をするための支援関数
	function ajax(httpMethod:string, path:string, postData:any, callback:IAjaxCallback){
		jQuery.ajax({
			cache: true,
			success: callback.success,
			error: (request, status, errorThrown)=>{ callback.error(status); },
			type: httpMethod.toUpperCase(),
			url: [baseURL, path].join("/"),
			data: postData,
		});
	}

	export class Threads{
		static get(opt:any, callback:IAjaxCallback){
			ajax("get", "threads", opt, callback);
		}
		static head(title:string, callback:IAjaxCallback){
			ajax("head", "threads", {
				"title": title,
			}, callback);
		}
		static post(title:string, callback:IAjaxCallback){
			ajax("post", "threads", {
				"title": title,
			}, callback);
		}
	}

	export class Records{
		static get(thread:Models.IRecordList, opt:any, callback:IAjaxCallback);
		static get(record:Models.IRecordInfo, opt:any, callback:IAjaxCallback);
		static get(argv1:any, opt:any, callback:IAjaxCallback){
			if(typeof argv1.record_id != "undefined"){
				var r = <Models.IRecordInfo>argv1;
				var path = ["records", r.thread_id, r.timestamp, r.record_id].join("/");
				ajax("get", path, opt, callback);
			}else{
				var t = <Models.IRecordList>argv1;
				var path = ["records", t.thread_id].join("/");
				ajax("get", path, opt, callback);
			}
		}
		static head(rec:Models.IRecordInfo, callback:IAjaxCallback){
			var path = ["records", rec.thread_id, rec.timestamp, rec.record_id].join("/");
			ajax("head", path, undefined, callback);
		}
		static post(thread_id:number, rec:Models.IRecord, callback:IAjaxCallback){
			var path = ["records", thread_id].join("/");
			ajax("post", path, rec, callback);
			// TODO: このままでは添付ファイルが処理できない・・・
		}
	}

	// 添付画像
	export class Attach{
		static getURL(rec:Models.RecordInfo):string{
			return [baseURL, "attach", rec.thread_id, rec.timestamp, rec.record_id].join("/");
		}
		static head(rec:Models.RecordInfo, callback:IAjaxCallback){
			ajax("head", this.getURL(rec), undefined, callback);
		}
	}
}

module Models.Filters{
	/****************************************************************
 	 * インタフェース
	 * IRecordListFilter
	 * IThreadListFilter
	****************************************************************/
	export interface IRecordListFilter{
		limit?:number;
		id?:string;
		start_time?:number;
		end_time?:number;
	}

	export interface IThreadListFilter{
		limit?:number;
		title?:string;
		start_time?:number;
		end_time?:number;
	}

	export interface IUnionFilter{
		recordList?: IRecordListFilter;
		threadList?: IThreadListFilter;
	}
}

module Models.Sorters{
	export interface IRecordCompareFunc{
		(a: Models.IRecord, b: Models.IRecord):number;
	}
	export interface IThreadCompareFunc{
		(a: Models.IThread, b: Models.IThread):number;
	}

	export interface IRecordListSorter{
		key?:string;
		compare?:IRecordCompareFunc;
	}
	export interface IThreadListSorter{
		key?:string;
		compare?:IThreadCompareFunc;
	}
}

module Models{
	/****************************************************************
 	 * インタフェース
	 * IRecordInfo
	 * IRecord
	 * IRecordList
	 *
	 * IThreadInfo
	 * IThread
	 * IThreadList
	****************************************************************/
	interface IList<t>{
		getAll(): t[];
		get(index:number): t;
	}

	export interface IRecordInfo{
		thread_id:number;
		record_id:string;
		timestamp:number;
	}

	export interface IRecord extends IRecordInfo{
		name:string;
		mail:string;
		body:string;
		attach:boolean;
		suffix:string;
	}

	export interface IRecordListOption{
		filter: Models.Filters.IRecordListFilter;
		sorter: Models.Sorters.IRecordListSorter;
		sanitizer: Security.Sanitizer;
	}
	export interface IRecordList extends IList<IRecord>{
		thread_id:number;
		sort();
		reload(callback:API.IAjaxCallback);
		update(callback:API.IAjaxCallback); // 最近の投稿のみ再取得
	}

	export interface IThreadInfo{
		id:number;
		title:string;
		timestamp:number; // 最終書き込み日時
		records:number;
		reload(callback:API.IAjaxCallback);
	}

	export interface IThread extends IThreadInfo{
		recordList:IRecordList;
		post(IRecord, callback:API.IAjaxCallback); // IRecordInfoのメンバは全てNULLでなければならない
		reload(callback:API.IAjaxCallback);
		update(callback:API.IAjaxCallback); // 最近の投稿のみ再取得
		get(filter:Models.Filters.IRecordListFilter):IRecordList;
	}

	export interface IThreadListOption{
		filter: Models.Filters.IThreadListFilter;
		sorter: Models.Sorters.IThreadListSorter;
		recordListOption: IRecordListOption;
	}

	export interface IThreadList extends IList<IThread>{
		sort();
		reload(callback:API.IAjaxCallback);
		add(title:string, callback:API.IAjaxCallback);
	}

	/****************************************************************
 	 * クラス
	 * RecordInfo
	 * Record
	 * Recordlist
	 *
	 * ThreadInfo
	 * Therad
	 * ThreadList
	****************************************************************/
	export class RecordInfo implements IRecordInfo{
		record_id:string;
		timestamp:number;

		constructor(public thread_id:number, record:any){
			this.record_id = record.id;
			this.timestamp = record.timestamp;
		}
		reload(callback:API.IAjaxCallback):IRecord{
			return null;
		}
	}

	export class Record extends RecordInfo implements IRecord{
		name:string;
		mail:string;
		body:string;
		attach:boolean;
		suffix:string;
		htmlName:string;
		htmlMail:string;
		htmlBody:string;
		fileUrl:string;
		fileType:string;

		constructor(thread_id:number, record:any, sanitizer){
			super(thread_id, record);
			this.name = record.name;
			this.mail = record.mail;
			this.body = record.body;
			this.attach = record.attach;
			this.suffix = record.suffix;

			this.htmlName = sanitizer.clean_string(this.name);
			this.htmlMail = sanitizer.clean_string(this.mail);
			this.htmlBody = sanitizer.clean_string(this.body);
			if(this.attach){
				this.fileUrl = API.Attach.getURL(this);
				this.fileType = {
					jpeg: "img",
					jpg: "img",
					png: "img",
					gif: "img",
				}[this.suffix] || "unknow";
			}else{
				this.fileUrl = this.fileType = null;
			}
		}
	}

	export class RecordList implements IRecordList{
		thread_id:number;
		private records:Array<IRecord>;

		constructor(thread:IThreadInfo, private option:IRecordListOption){
			this.thread_id = thread.id;
		}

		getAll(): IRecord[]{
			return this.records;
		}
		get(i:number): IRecord{
			return this.records[i];
		}
		private converter(json):Array<Record>{
			var records = [];
			for(var i in json.records){
				records.push(new Record(this.thread_id, json.records[i], this.option.sanitizer));
			}
			return records;
		}
		sort(){
			var func: Models.Sorters.IRecordCompareFunc;
			if(! this.option.sorter){
				return;
			}
			if(this.option.sorter.key){
				var funcList = {
					timestamp: (a: IRecord, b: IRecord)=>{ return b.timestamp - a.timestamp; },
				};
				func = funcList[this.option.sorter.key];
			}else{
				func = this.option.sorter.compare;
			}

			if(func){
				this.records.sort(func);
			}
		}
		reload(callback:API.IAjaxCallback){
			var preCallback:API.IAjaxCallback = {
				"success": (data)=>{
					this.records = this.converter(data);
					this.sort();
					callback.success(this);
				},
				"error": callback.error,
			};
			API.Records.get(this, this.option.filter, preCallback);
		}
		// 最近の投稿を取得
		update(callback:API.IAjaxCallback){
			var endTime = this.option.filter.end_time || Math.floor((new Date()).getTime()/1000);
			var timeRange = 24 * 60*60;
			var extendRange = true;
			var records = [];

			var loop = ()=>{
				var filter = jQuery.extend({}, this.option.filter);
				filter.start_time = Math.max(endTime - timeRange, this.option.filter.start_time || 0);
				filter.end_time = endTime;

				// ループ終了
				// 十分な数のレコードを取得できなかった
				if(filter.end_time < filter.start_time){
					this.records = records;
					this.sort();
					callback.success(this);
					return;
				}

				API.Records.get(this, filter, {
					"success": (data)=>{
						var rec = this.converter(data);
						if(! filter.limit){
							this.records = rec;
							this.sort();
							callback.success(this);
							 // ループ終了
						}else if(rec.length >= filter.limit){
							// 新しいレコードが取得できていない
							// 範囲を制限して再取得
							timeRange = Math.floor(timeRange / 4);
							extendRange = false;
							loop();
						}else if(records.length + rec.length >= filter.limit){
							// 十分な数のレコードを取得できた
							this.records = records.concat(rec).slice(0, filter.limit);
							this.sort();
							callback.success(this);
							 // ループ終了
						}else{
							this.records = records = records.concat(rec);

							// 取得範囲を過去の方向へ移動させてから再取得
							// 高々4回で取得できるはず
							endTime -= timeRange;
							if(extendRange){
								timeRange *= 10;
							}
							loop();
						}
					},
					"error": callback.error,
				});
			};
			loop();
		}
	}

	export class ThreadInfo implements IThreadInfo{
		id:number;
		title:string;
		timestamp:number;
		records:number;

		constructor(threadInfo:IThreadInfo){
			this.id = threadInfo.id;
			this.title = threadInfo.title;
			this.timestamp = threadInfo.timestamp;
			this.records = threadInfo.records;
		}

		reload(callback:API.IAjaxCallback){
			var opt = {
				"title": this.title
			};
			var cb = {
				success: (data)=>{
					this.id = data.threads[0].id;
					this.title = data.threads[0].title;
					this.timestamp = data.threads[0].timestamp;
					this.records = data.threads[0].records;
					callback.success(this);
				},
				error: callback.error,
			};
			API.Threads.get(opt, cb);
		}
	}

	export class Thread extends ThreadInfo implements IThread{
		recordList:IRecordList;

		constructor(thread:IThreadInfo, private option:IRecordListOption){
			super(<IThreadInfo>thread);
			this.recordList = new RecordList(this, option);
		}

		post(rec:IRecord, callback:API.IAjaxCallback){
			API.Records.post(this.id, rec, callback);
		}
		reload(callback:API.IAjaxCallback){
			this.recordList.reload(callback);
		}
		update(callback:API.IAjaxCallback){
			this.recordList.update(callback);
		}
		get(filter:Models.Filters.IRecordListFilter):IRecordList{
			return this.recordList;
		}
	}

	export class ThreadList implements IThreadList{
		private threads:Array<IThread> = [];
		public filter:Models.Filters.IUnionFilter;;

		constructor(private option: IThreadListOption){
			this.filter = option.filter || {};
		}

		getAll(): IThread[]{
			return this.threads;
		}
		get(i:number): IThread{
			return this.threads[i];
		}

		sort(){
			var func: Models.Sorters.IThreadCompareFunc;
			if(! this.option.sorter){
				return;
			}
			if(this.option.sorter.key){
				var funcList = {
					title: (a: IThread, b: IThread)=>{ return a.title.localeCompare(b.title); },
					timestamp: (a: IThread, b: IThread)=>{ return b.timestamp - a.timestamp; },
					records: (a: IThread, b: IThread)=>{ return b.records - a.records; },
				};
				func = funcList[this.option.sorter.key];
			}else{
				func = this.option.sorter.compare;
			}

			if(func){
				this.threads.sort(func);
			}
		}
		private converter(json):Array<IThread>{
			var threads = [];
			if(json.threads){
				for(var i in json.threads){
					var th = json.threads[i];
					threads.push(new Thread(th, this.option.recordListOption));
				}
			}else if(json.thread){
				var th = json.thread;
				threads.push(new Thread(th, this.option.recordListOption));
			}
			return threads;
		}
		reload(callback:API.IAjaxCallback){
			API.Threads.get(this.filter.threadList, {
				success: (data)=>{
					this.threads = this.converter(data);
					this.sort();
					callback.success(this);
				},
				error: callback.error,
			});
		}
		add(title:string, callback:API.IAjaxCallback){
			var preCallback = <API.IAjaxCallback>{
				"success": (json)=>{
					var th = this.converter(json)[0];
					this.threads.push(th);
					this.sort();
					return callback.success(th);
				},
				"error": callback.error,
			};
			API.Threads.post(title, preCallback);
		}
	}
}

module Controllers{
	enum MainViewType{
		"createThread",
		"thread",
	}
	enum MenuViewType{
		"tag",
		"thread",
	}

	interface INewThread{
		title: string;
	}
	interface IView{
		main: MainViewType;
	}

	interface INewRecord extends Models.IRecord{}
	interface INewRecordForm{
		isOpen: boolean;
	}

	interface IScope extends angular.IScope{
		MainViewType: any;
		MenuViewType: any;
		viewStatus: IView;

		threads: Models.IThreadList;
		currentThread: Models.IThread;
		tags: any[];

		setCurrentThread(thread:Models.Thread): void;
		switchMainView(viewType:MainViewType): void;
		setMenuViewType(viewType:MenuViewType): void;

		newRecord: INewRecord;
	}
	interface IPostFormScope extends IScope{
		useFullScreen: boolean;
		newThread: INewThread;
		newRecordForm: INewRecordForm;

		postThread(): void;
		postRecord(): void;
		showPostForm(event): void;
		focus(event): void;
	}
	interface IPostFormDialogScope extends angular.IScope{
		newRecord: INewRecord;

		hide(): void;
		cancel(): void;
		post(): void;
	}

	export class MikaCtrl{
		constructor(private $scope:IScope, $sce){
			$scope.MainViewType = MainViewType;
			$scope.viewStatus = {
				main: MainViewType.thread,
			};

			$scope.newRecord = <INewRecord>{
				"name": null,
				"mail": null,
				"body": null,
				"attach": null,
				"suffix": null,
			};

			$scope.setCurrentThread = (thread:Models.Thread)=>{this.setCurrentThread(thread);};
			$scope.switchMainView = (viewType:MainViewType)=>{this.switchMainView(viewType);};

			var tl = new Models.ThreadList({
				filter: {
					limit: 100,
				},
				sorter: {
					key: "timestamp",
				},
				recordListOption: {
					filter: {
						limit: 100,
					},
					sorter: {
						key: "timestamp",
					},
					sanitizer: new Security.RecordSanitizer($sce),
				},
			});
			tl.reload({
				"success": ()=>{
					$scope.threads = tl;
					$scope.currentThread = tl.get(0);
					if($scope.currentThread){
						$scope.currentThread.update({
							"success": ()=>{
								$scope.$apply();
							},
							"error": ()=>{return;},
						});
					}else{
						$scope.switchMainView(MainViewType.createThread);
					}
					$scope.$apply();
				},
				"error": ()=>{return;},
			});
		}

		setCurrentThread(thread){
			this.$scope.currentThread = thread;
			this.switchMainView(MainViewType.thread);
			if(this.$scope.currentThread){
				this.$scope.currentThread.update({
					"success": ()=>{
						this.$scope.$apply();
					},
					"error": ()=>{return;},
				});
			}
		}
		switchMainView(viewType:MainViewType){
			this.$scope.viewStatus.main = viewType;
			if(this.$scope.viewStatus.main != MainViewType.thread){
				this.$scope.currentThread = null;
			}
		}
	}

	export class ThreadCtrl{
		constructor(private $scope:IPostFormScope, private $rootScope, private $mdMedia, private $mdDialog){
			$scope.newThread = <INewThread>{
				"title": null,
			};
			$scope.newRecordForm = {
				isOpen: false,
			};
			$scope.postThread = ()=>{return this.postThread();};
			$scope.postRecord = ()=>{return this.postRecord();};

			$scope.showPostForm = (ev)=>{return this.showPostForm(ev);};
			$scope.$watch(()=>{
				return $mdMedia("xs") || $mdMedia("sm");
			}, (useFullScreen)=>{
				$scope.useFullScreen = useFullScreen === true;
			});
			$scope.focus = (event)=>{
				$scope.newRecordForm.isOpen = true;
			};
		}

		postThread(){
			this.$scope.threads.add(this.$scope.newThread.title, <API.IAjaxCallback>{
				"success": (thread)=>{
					this.$scope.setCurrentThread(thread);
					this.$scope.newThread.title = null;
					this.$rootScope.$apply();
				},
				"error": ()=>{return;},
			});
			return false;
		}

		postRecord(){
			var callback = <API.IAjaxCallback>{
				"success": ()=>{
					this.$scope.currentThread.update({
						"success": ()=>{
							this.$scope.newRecord.body = "";
							this.$scope.$apply();
						},
						"error": ()=>{return;},
					});
				},
				"error": ()=>{return;},
			};
			var record = this.$scope.newRecord;
			this.$scope.currentThread.post(record, callback);
		}

		showPostForm(event){
			this.$mdDialog.show({
				controller: PostFormDialogCtrl,
				template: angular.element("#postFormDialog").html(),
				parent: angular.element(".mika"),
				targetEvent: event,
				clickOutsideToClose: true,
				fullscreen: this.$scope.useFullScreen,
				scope: this.$scope.$new(),
			}).then((ret)=>{
				// post button clicked.
				this.postRecord();
			}, ()=>{
				// cancelled.
			});
		};

	}
	export class PostFormDialogCtrl{
		constructor(private $scope:IPostFormDialogScope, private $mdDialog){
			$scope.hide = ()=>{return this.hide();};
			$scope.cancel = ()=>{return this.cancel();};
			$scope.post = ()=>{return this.post();};
		}

		hide(){
			this.$mdDialog.hide();
		}
		cancel(){
			this.$mdDialog.cancel();
		}
		post(){
			this.$mdDialog.hide("post");
		}
	}
}

angular.module("mika", ["ngSanitize", "ngMaterial", "relativeDate"])
.controller("MikaCtrl", Controllers.MikaCtrl)
.controller("ThreadCtrl", Controllers.ThreadCtrl);

