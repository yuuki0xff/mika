
declare interface ISanitizeConfig{
	elements?: string[];
	attributes?: string[];
	allow_comments?: boolean;
	protocols?: string[][];
	add_attributes?: string[];
	remove_element_contents?: boolean[];
	remove_all_contents?: boolean[];
}

declare interface ISanitizePresetConfig{
	BASIC: ISanitizeConfig;
	RELAXED: ISanitizeConfig;
	RESTRICTED: ISanitizeConfig;
}

declare class Sanitize{
	REGEX_PROTOCOL: string;
	RELATIV: string;
	ALL: string;

	config: ISanitizeConfig;
	static Config: ISanitizePresetConfig;

	constructor(config?: ISanitizeConfig);
	clean_node(container: DocumentFragment): DocumentFragment;
}

