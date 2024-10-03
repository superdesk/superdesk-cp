import * as React from 'react';
import {ISearchPanelWidgetProps, ISuperdesk} from 'superdesk-api';

type IMediaType = 'Image' | 'Video';

interface IParams {
    from: string;
    to: string;
    mediaTypes: {
        [key in IMediaType]?: boolean;
    };
};

interface IMediaTypeLabel {
    type: IMediaType,
    label: string;
}

export const searchPanelWidgetFactory = (
    gettext: ISuperdesk['localization']['gettext'],
): React.ComponentType<ISearchPanelWidgetProps<IParams>> => {
    const mediaTypes: Array<IMediaTypeLabel> = [
        {
            type: 'Image',
            label: gettext('Picture'),
        },
        {
            type: 'Video',
            label: gettext('Video'),
        },
    ];

    return class SearchPanelWidget extends React.PureComponent<ISearchPanelWidgetProps<IParams>> {
        toggleMediaType(type: IMediaType) {
            const mediaTypes = this.props.params.mediaTypes || {};

            mediaTypes[type] = !mediaTypes[type];
            this.props.setParams({mediaTypes});
        }

        isActive(type: IMediaType) {
            return this.props.params.mediaTypes != null && this.props.params.mediaTypes[type] === true;
        }

        render() {
            const {params} = this.props;

            if (this.props.provider !== 'orangelogic') {
                return null;
            }

            return (
                <fieldset>
                    <div className="field flex-grid flex-grid--boxed-small flex-grid--small-2 sd-margin-t--2">
                        {mediaTypes.map((type) => (
                            <button
                                key={type.type}
                                className={'toggle-button' + (this.isActive(type.type) ? ' toggle-button--active' : '')}
                                onClick={() => this.toggleMediaType(type.type)}
                            >
                                {type.label}
                            </button>
                        ))}
                    </div>
                    <div className="field">
                        <label className="search-label">{gettext('From')}</label>
                        <input type="date" value={params.from || ''}
                            onChange={(event) => this.props.setParams({from: event.target.value})}
                        />
                    </div>
                    <div className="field">
                        <label className="search-label">{gettext('To')}</label>
                        <input type="date" value={params.to || ''}
                            onChange={(event) => this.props.setParams({to: event.target.value})}
                        />
                    </div>
                </fieldset>
            );
        }
    };
};
