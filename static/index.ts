/// <reference path="./typings/jquery/jquery.d.ts" />
/// <reference path="./typings/angularjs/angular.d.ts" />

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
				var t = <Models.IThreadInfo>argv1;
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
		limit:number;
		id:string;
		start_time:number;
		end_time:number;
	}

	export interface IThreadListFilter{
		limit:number;
		title:string;
		start_time:number;
		end_time:number;
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
	}

	export interface IRecordList extends IList<IRecord>{
		thread_id:number;
		filter:Models.Filters.IRecordListFilter;
		reload(callback:API.IAjaxCallback);
	}

	export interface IThreadInfo{
		id:number;
		title:string;
		timestamp:number; // 最終書き込み日時
		recordCount:number;
		reload(callback:API.IAjaxCallback);
	}

	export interface IThread extends IThreadInfo{
		recordList:IRecordList;
		post(IRecord, callback:API.IAjaxCallback); // IRecordInfoのメンバは全てNULLでなければならない
		reload(callback:API.IAjaxCallback);
		update(callback:API.IAjaxCallback); // 最近の投稿のみ再取得
		get(filter:Models.Filters.IRecordListFilter):IRecordList;
	}

	export interface IThreadList extends IList<IThread>{
		reload(callback:API.IAjaxCallback);
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

		constructor(thread_id:number, record:any){
			super(thread_id, record);
			this.name = record.name;
			this.mail = record.mail;
			this.body = record.body;
			this.attach = record.attach;
		}
	}

	export class RecordList{
		thread_id:number;
		private records:Array<IRecord>;

		constructor(thread:IThreadInfo, public filter:Models.Filters.IRecordListFilter=undefined){
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
				records.push(new Record(this.thread_id, json.threads[i]));
			}
			return records;
		}
		reload(callback:API.IAjaxCallback){
			var opt = {};
			var preCallback:API.IAjaxCallback = {
				"success": (data)=>{
					var rec = this.converter(data);
					console.dir(rec);
					callback.success(rec);
				},
				"error": callback.error,
			};
			if(this.filter){
				for(var key in "limit id start_time end_time".split(" ")){
					if(this.filter[key]){
						opt[key] = this.filter[key];
					}
				}
			}
			API.Records.get(this, opt, preCallback);
		}
	}

	export class ThreadInfo implements IThreadInfo{
		id:number;
		title:string;
		timestamp:number;
		recordCount:number;

		constructor(threadInfo:IThreadInfo){
			this.id = threadInfo.id;
			this.title = threadInfo.title;
			this.timestamp = threadInfo.timestamp;
			this.recordCount = threadInfo.recordCount;
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
					this.recordCount = data.threads[0].recordCount;
					callback.success(this);
				},
				error: callback.error,
			};
			API.Threads.get(opt, cb);
		}
	}

	export class Thread extends ThreadInfo implements IThread{
		recordList:IRecordList;

		constructor(thread:IThreadInfo){
			super(<IThreadInfo>thread);
			this.recordList = new RecordList(this);
		}

		post(rec:IRecord, callback:API.IAjaxCallback){
			API.Records.post(this.id, rec, callback);
		}
		reload(callback:API.IAjaxCallback){
			this.recordList.reload(callback);
		}
		update(callback:API.IAjaxCallback){
			var opt = {
				"limit": 1000,
			};
			// TODO:
//             API.Records.get(<IThreadInfo>this, opt, callback);
		}
		get(filter:Models.Filters.IRecordListFilter):IRecordList{
			return this.recordList;
		}
	}

	export class ThreadList implements IThreadList{
		private threads:Array<IThread> = [];

		constructor(public filter:Models.Filters.IThreadListFilter=undefined){}

		getAll(): IThread[]{
			return this.threads;
		}
		get(i:number): IThread{
			return this.threads[i];
		}

		private converter(json):Array<IThread>{
			var threads = [];
			for(var i in json.threads){
				var th = json.threads[i];
				threads.push(new Thread(th));
			}
			return threads;
		}
		reload(callback:API.IAjaxCallback){
			var opt = {};
			if(this.filter){
				for(var key in "limit title start_time end_time".split(" ")){
					if(this.filter[key]){
						opt[key] = this.filter[key];
					}
				}
			}
			API.Threads.get(opt, {
				success: (data)=>{
					this.threads = this.converter(data);
					callback.success(this);
				},
				error: callback.error,
			});
		}
	}
}

module Controllers{
	enum MainViewType{
		"threadList",
		"thread",
		"newThread",
	}
	enum MenuViewType{
		"tag",
		"thread",
	}

	interface IScope extends angular.IScope{
		MainViewType: any;
		mainView: MainViewType;
		MenuViewType: any;
		menuView: MenuViewType;

		threads: Models.IThreadList;
		currentThread: Models.IThread;
		tags: any[];

		setCurrentThread(thread:Models.Thread): void;
		switchMainView(viewType:MainViewType): void;
		setMenuViewType(viewType:MenuViewType): void;
	}

	export class MikaCtrl{
		constructor(private $scope:IScope){
			$scope.MainViewType = MainViewType;
			$scope.mainView = MainViewType.thread;

			$scope.setCurrentThread = (thread:Models.Thread)=>{this.setCurrentThread(thread);};
			$scope.switchMainView = (viewType:MainViewType)=>{this.switchMainView(viewType);};
		}

		setCurrentThread(thread){
			this.$scope.currentThread = thread;
			this.switchMainView(MainViewType.thread);
		}
		switchMainView(viewType:MainViewType){
			this.$scope.mainView = viewType;
			if(this.$scope.mainView != MainViewType.thread){
				this.$scope.currentThread = null;
			}
		}
	}

	export class MenuCtrl{
		constructor(private $scope:IScope){
			$scope.MenuViewType = MenuViewType;
			$scope.menuView = MenuViewType.thread;

			$scope.setMenuViewType = (viewType:MenuViewType)=>{this.setMenuViewType(viewType);};
		}

		setMenuViewType(viewType:MenuViewType){
			this.$scope.menuView = viewType;
		}
	}

	export class ThreadCtrl{}
}

angular.module("mika", [])
.controller("MikaCtrl", Controllers.MikaCtrl)
.controller("MenuCtrl", Controllers.MenuCtrl)
.controller("ThreadCtrl", Controllers.ThreadCtrl);

